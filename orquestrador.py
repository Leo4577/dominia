#!/usr/bin/env python3
"""
Orquestrador JUZIA — ciclo completo, incremental e idempotente.
Roda semanalmente (cron): coleta janela nova -> grava documento ->
extrai só o que ainda NÃO tem decisão -> grava decisao. Não reprocessa o que já existe.

Env necessárias:
    DATABASE_URL        postgres do Supabase
    ANTHROPIC_API_KEY   chave da IA
Opcionais:
    GRUPO=AEREO         grupo de tese (por ora AEREO validado)
    JANELA_DIAS=21      coleta acórdãos publicados nos últimos N dias
    MAX_POR_FRASE=400   teto por frase de busca
    MODEL_A / MODEL_B   modelos extrator/auditor
"""
import os, sys, json, time, hashlib, unicodedata, re, urllib.request
import datetime as dt
import anthropic, psycopg2
from psycopg2.extras import execute_batch
from teses_config import config   # <- frases, schema e prompt por grupo

EP="https://jurisprudenciaws.tjba.jus.br/graphql"
GRUPO=os.environ.get("GRUPO","AEREO")
JANELA=int(os.environ.get("JANELA_DIAS","21"))
MAXF=int(os.environ.get("MAX_POR_FRASE","400"))
MODEL_A=os.environ.get("MODEL_A","claude-sonnet-5")
MODEL_B=os.environ.get("MODEL_B","claude-opus-5")

CFG=config(GRUPO)
FRASES=CFG["frases"]; SCHEMA=CFG["schema"]; SYS=CFG["system"]

# ---------- coleta ----------
Q=("query f($f:DecisaoFilter!,$p:Int!,$i:Int!){ filter(decisaoFilter:$f,pageNumber:$p,itemsPerPage:$i){ "
   "decisoes{ numeroProcesso tipoDecisao dataJulgamento dataPublicacao orgaoJulgador{ nome } relator{ nome } classe{ descricao } conteudo } } }")
def norm(s): return re.sub(r"\s+"," ",unicodedata.normalize("NFKD",s or "").encode("ascii","ignore").decode().lower()).strip()
def mkf(a,di): return {"assunto":a,"numeroRecurso":"","orgaos":[],"relatores":[],"classes":[],"dataInicial":di,"dataFinal":None,
   "segundoGrau":False,"turmasRecursais":True,"tipoAcordaos":True,"tipoDecisoesMonocraticas":True,"ordenadoPor":"dataPublicacao"}
def gql(a,p,di,i=30):
    body=json.dumps({"query":Q,"variables":{"f":mkf(a,di),"p":p,"i":i}}).encode()
    r=urllib.request.Request(EP,data=body,method="POST",headers={"content-type":"application/json","origin":"https://jurisprudencia.tjba.jus.br","referer":"https://jurisprudencia.tjba.jus.br/"})
    for _ in range(3):
        try:
            with urllib.request.urlopen(r,timeout=90) as x: d=json.loads(x.read())
            if d.get("errors"): raise RuntimeError(d["errors"][0]["message"])
            return d["data"]["filter"]["decisoes"] or []
        except Exception as e: last=e; time.sleep(2)
    raise last
CLS_EXCLUI=["embargos de declaracao","cumprimento de sentenca","agravo","execucao","mandado","conflito"]
CONT_EXCLUI=["cumprimento de sentenca","embargos de declaracao","juizo de admissibilidade"]
def eh_merito(classe,cont):
    c=norm(classe)
    if any(x in c for x in CLS_EXCLUI): return False
    if c and "recurso inominado" not in c: return False
    return not any(x in norm(cont)[:400] for x in CONT_EXCLUI)

def coletar(di):
    vis={}
    for a in FRASES:
        got=0; p=1
        while got<MAXF:
            decs=gql(a,p,di)
            if not decs: break
            for x in decs:
                pn=x.get("numeroProcesso")
                if not pn or pn in vis: got+=1; continue
                cont=x.get("conteudo") or ""
                if not eh_merito((x.get("classe") or {}).get("descricao") or "", cont): got+=1; continue
                vis[pn]={"numeroProcesso":pn,"tipoDecisao":x.get("tipoDecisao"),
                    "classe":(x.get("classe") or {}).get("descricao"),
                    "orgaoJulgador":(x.get("orgaoJulgador") or {}).get("nome"),
                    "relator":(x.get("relator") or {}).get("nome"),
                    "dataJulgamento":(x.get("dataJulgamento") or "")[:10] or None,
                    "dataPublicacao":(x.get("dataPublicacao") or "")[:10] or None,
                    "conteudo":cont,"_frase":a.strip('"')}
                got+=1
            p+=1; time.sleep(0.25)
        print(f"  coletado {a}: parcial", file=sys.stderr)
    return list(vis.values())

# ---------- extração (2 modelos) — SCHEMA e SYS vêm de teses_config ----------
def extrai(cli,model,cont):
    r=cli.messages.create(model=model,max_tokens=1500,system=SYS,
        output_config={"format":{"type":"json_schema","schema":SCHEMA}},
        messages=[{"role":"user","content":f"Extraia os dados deste acórdão:\n\n{cont[:18000]}"}])
    return json.loads(next(b.text for b in r.content if b.type=="text"))

# ---------- banco ----------
def db():
    u=os.environ.get("DATABASE_URL") or sys.exit("Defina DATABASE_URL")
    return psycopg2.connect(u)

def upsert_docs(cur, docs):
    sql="""insert into documento (numero_processo,fonte,instancia,tese_busca,orgao_julgador,relator,classe,tipo_decisao,data_julgamento,data_publicacao,conteudo,hash)
      values (%s,'TJBA','TURMAS_RECURSAIS',%s,%s,%s,%s,%s,%s,%s,%s,%s)
      on conflict (numero_processo) do update set conteudo=excluded.conteudo, hash=excluded.hash, data_publicacao=excluded.data_publicacao;"""
    data=[(d["numeroProcesso"],d["_frase"],d["orgaoJulgador"],d["relator"],d["classe"],d["tipoDecisao"],
           d["dataJulgamento"],d["dataPublicacao"],d["conteudo"],hashlib.md5(d["conteudo"].encode()).hexdigest()) for d in docs]
    execute_batch(cur,sql,data,page_size=100)

def pendentes(cur):
    cur.execute("""select d.id, d.numero_processo, d.orgao_julgador, d.relator, d.conteudo
                   from documento d left join decisao dc on dc.documento_id=d.id
                   where dc.id is null and d.tese_busca = any(%s)""",([f.strip('"') for f in FRASES],))
    return cur.fetchall()

def upsert_decisao(cur, doc_id, np, org, rel, a, concord):
    cur.execute("""insert into decisao (documento_id,numero_processo,tese_grupo,micro_tese,e_merito,resultado_consumidor,
        dano_moral_concedido,dano_moral_valor,dano_material_concedido,fundamentos,provas,comarca,vara_origem,confianca,
        concordancia_modelos,modelo_extrator,relator,orgao_julgador)
        values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        on conflict (documento_id) do update set micro_tese=excluded.micro_tese, resultado_consumidor=excluded.resultado_consumidor,
        e_merito=excluded.e_merito, dano_moral_concedido=excluded.dano_moral_concedido, dano_moral_valor=excluded.dano_moral_valor,
        dano_material_concedido=excluded.dano_material_concedido, fundamentos=excluded.fundamentos, provas=excluded.provas,
        comarca=excluded.comarca, vara_origem=excluded.vara_origem, confianca=excluded.confianca,
        concordancia_modelos=excluded.concordancia_modelos, extraido_em=now();""",
        (doc_id,np,GRUPO,a["micro_tese"],bool(a["e_merito"]),a["resultado_consumidor"],
         a["dano_moral_concedido"],a["dano_moral_valor_reais"] or None,a["dano_material_concedido"],
         a["fundamentos"],a["prova_decisiva"],a.get("comarca"),a.get("vara_origem"),a["confianca"],
         concord,f"{MODEL_A}+{MODEL_B}",rel,org))

def main():
    di=(dt.date.today()-dt.timedelta(days=JANELA)).isoformat()
    print(f"[{GRUPO}] janela desde {di} (últimos {JANELA} dias)", file=sys.stderr)
    docs=coletar(di)
    print(f"coletados (mérito, dedup): {len(docs)}", file=sys.stderr)
    con=db(); cur=con.cursor()
    upsert_docs(cur,docs); con.commit()
    pend=pendentes(cur)
    print(f"pendentes de extração: {len(pend)}", file=sys.stderr)
    cli=anthropic.Anthropic(); ok=0; conc=0
    for i,(doc_id,np,org,rel,cont) in enumerate(pend,1):
        try:
            a=extrai(cli,MODEL_A,cont); b=extrai(cli,MODEL_B,cont)
        except Exception as e:
            print(f"  [{i}] ERRO {np}: {e}", file=sys.stderr); continue
        concord = (a["micro_tese"]==b["micro_tese"] and a["resultado_consumidor"]==b["resultado_consumidor"])
        if concord: conc+=1
        upsert_decisao(cur,doc_id,np,org,rel,a,concord); con.commit(); ok+=1
        if i%20==0: print(f"  extraídos {i}/{len(pend)}", file=sys.stderr)
        time.sleep(0.2)
    cur.close(); con.close()
    print(f"OK: +{ok} decisões ({conc} concordantes / {round(100*conc/ok) if ok else 0}%). Base atualizada.", file=sys.stderr)

if __name__=="__main__": main()
