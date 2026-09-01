#!/usr/bin/env python3
"""
Carregador JUZIA -> Supabase/Postgres (upsert idempotente).

Pré-requisito:
    pip install psycopg2-binary
    export DATABASE_URL="postgresql://postgres:SENHA@db.SEUPROJETO.supabase.co:5432/postgres"
    (Supabase -> Project Settings -> Database -> Connection string -> URI)

Uso:
    # 1) carrega os acórdãos crus (corpus limpo do coletar_aereo.py)
    python3 carregar_supabase.py docs aereo_limpo.jsonl

    # 2) carrega a extração estruturada (saída do pipeline_aereo.py)
    python3 carregar_supabase.py decisoes aereo_estruturado.jsonl --grupo AEREO
"""
import os, sys, json, argparse, hashlib
import psycopg2
from psycopg2.extras import execute_batch

def conn():
    url=os.environ.get("DATABASE_URL")
    if not url: sys.exit("Defina DATABASE_URL (connection string do Supabase).")
    return psycopg2.connect(url)

def d10(s):  # ISO -> date (YYYY-MM-DD) ou None
    return (s or "")[:10] or None

def carregar_docs(path):
    rows=[json.loads(l) for l in open(path,encoding="utf-8")]
    c=conn(); cur=c.cursor(); n=0
    sql="""
      insert into documento
        (numero_processo, fonte, instancia, tese_busca, orgao_julgador, relator,
         classe, tipo_decisao, data_julgamento, conteudo, hash)
      values (%s,'TJBA','TURMAS_RECURSAIS',%s,%s,%s,%s,%s,%s,%s,%s)
      on conflict (numero_processo) do update set
        orgao_julgador=excluded.orgao_julgador, relator=excluded.relator,
        classe=excluded.classe, tipo_decisao=excluded.tipo_decisao,
        data_julgamento=excluded.data_julgamento, conteudo=excluded.conteudo, hash=excluded.hash;
    """
    data=[]
    for r in rows:
        cont=r.get("conteudo") or ""
        data.append((r.get("numeroProcesso"), (r.get("_frase") or "").strip('"'),
                     r.get("orgaoJulgador"), r.get("relator"), r.get("classe"),
                     r.get("tipoDecisao"), d10(r.get("dataJulgamento")), cont,
                     hashlib.md5(cont.encode("utf-8")).hexdigest()))
    execute_batch(cur, sql, data, page_size=100); n=len(data)
    c.commit(); cur.close(); c.close()
    print(f"documento: {n} upserts")

def carregar_decisoes(path, grupo):
    rows=[json.loads(l) for l in open(path,encoding="utf-8")]
    c=conn(); cur=c.cursor(); ok=0; semdoc=0
    sql="""
      insert into decisao
        (documento_id, numero_processo, relator, orgao_julgador, tese_grupo, micro_tese, e_merito,
         resultado_consumidor, dano_moral_concedido, dano_moral_valor, dano_material_concedido,
         fundamentos, provas, comarca, vara_origem, sumula_estrategica, confianca,
         concordancia_modelos, modelo_extrator)
      select id, %(np)s, %(rel)s, %(org)s, %(grp)s, %(mt)s, %(mer)s, %(res)s, %(dmc)s, %(dmv)s, %(dmat)s,
             %(fund)s, %(prov)s, %(com)s, %(vara)s, %(sum)s, %(conf)s, %(conc)s, %(mod)s
      from documento where numero_processo = %(np)s
      on conflict (documento_id) do update set
        relator=excluded.relator, orgao_julgador=excluded.orgao_julgador,
        tese_grupo=excluded.tese_grupo, micro_tese=excluded.micro_tese, e_merito=excluded.e_merito,
        resultado_consumidor=excluded.resultado_consumidor, dano_moral_concedido=excluded.dano_moral_concedido,
        dano_moral_valor=excluded.dano_moral_valor, dano_material_concedido=excluded.dano_material_concedido,
        fundamentos=excluded.fundamentos, provas=excluded.provas, comarca=excluded.comarca,
        vara_origem=excluded.vara_origem, sumula_estrategica=excluded.sumula_estrategica,
        confianca=excluded.confianca, concordancia_modelos=excluded.concordancia_modelos,
        modelo_extrator=excluded.modelo_extrator, extraido_em=now();
    """
    for r in rows:
        np=r.get("numeroProcesso")
        p={"np":np,"rel":r.get("relator"),"org":r.get("orgaoJulgador"),"grp":grupo,"mt":r.get("micro_tese"),
           "mer":bool(r.get("e_merito_aereo",True)),
           "res":r.get("resultado_consumidor"),
           "dmc":r.get("dano_moral_concedido"),
           "dmv":r.get("dano_moral_valor_reais") or None,
           "dmat":r.get("dano_material_concedido"),
           "fund":r.get("fundamentos") or [], "prov":r.get("prova_decisiva") or r.get("provas") or [],
           "com":r.get("comarca"),"vara":r.get("vara_origem"),
           "sum":r.get("sumula_estrategica"),"conf":r.get("confianca"),
           "conc":bool(r.get("_concordancia",False)),
           "mod":r.get("modelo_extrator") or "sonnet-5+opus-5"}
        cur.execute(sql,p)
        if cur.rowcount: ok+=1
        else: semdoc+=1
    c.commit(); cur.close(); c.close()
    print(f"decisao: {ok} upserts | {semdoc} sem documento correspondente (rode 'docs' antes)")

def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("docs"); a.add_argument("jsonl")
    b=sub.add_parser("decisoes"); b.add_argument("jsonl"); b.add_argument("--grupo",default="AEREO")
    args=ap.parse_args()
    if args.cmd=="docs": carregar_docs(args.jsonl)
    else: carregar_decisoes(args.jsonl, args.grupo)

if __name__=="__main__": main()
