#!/usr/bin/env python3
"""
Passo 1 do pipeline validado — coleta + dedup + filtro de mérito (tese AÉREO).
Nao usa IA. Produz o corpus LIMPO sobre o qual a % sera calculada.

Uso:
    python3 coletar_aereo.py --max-por-frase 200 --out aereo_limpo.jsonl
"""
import json, urllib.request, time, unicodedata, re, sys, argparse

EP="https://jurisprudenciaws.tjba.jus.br/graphql"
Q=("query f($f:DecisaoFilter!,$p:Int!,$i:Int!){ filter(decisaoFilter:$f,pageNumber:$p,itemsPerPage:$i){ "
   "itemCount decisoes{ numeroProcesso tipoDecisao dataJulgamento orgaoJulgador{ nome } relator{ nome } classe{ descricao } conteudo } } }")
DI="2023-08-18"

# frases da tese aereo (COM acento — a API exige)
FRASES=['"extravio de bagagem"','"atraso de voo"','"cancelamento de voo"','"overbooking"','"bagagem danificada"']

def mk(a):
    return {"assunto":a,"numeroRecurso":"","orgaos":[],"relatores":[],"classes":[],"dataInicial":DI,"dataFinal":None,
            "segundoGrau":False,"turmasRecursais":True,"tipoAcordaos":True,"tipoDecisoesMonocraticas":True,"ordenadoPor":"dataPublicacao"}
def norm(s):
    return re.sub(r"\s+"," ",unicodedata.normalize("NFKD",s or "").encode("ascii","ignore").decode().lower()).strip()
def page(a,p,i=30):
    body=json.dumps({"query":Q,"variables":{"f":mk(a),"p":p,"i":i}}).encode()
    r=urllib.request.Request(EP,data=body,method="POST",headers={"content-type":"application/json","origin":"https://jurisprudencia.tjba.jus.br","referer":"https://jurisprudencia.tjba.jus.br/"})
    for _ in range(3):
        try:
            with urllib.request.urlopen(r,timeout=90) as x: d=json.loads(x.read())
            if d.get("errors"): raise RuntimeError(d["errors"][0]["message"])
            return d["data"]["filter"]
        except Exception as e:
            last=e; time.sleep(2)
    raise last

# --- filtro de mérito: mantém só o recurso inominado de mérito ---
CLASSE_MERITO = "recurso inominado"
CLASSE_EXCLUI = ["embargos de declaracao","cumprimento de sentenca","agravo","execucao","carta precatoria",
                 "mandado de seguranca","conflito","peticao","habeas"]
CONTEUDO_EXCLUI = ["cumprimento de sentenca","embargos de declaracao","embargos declaratorios",
                   "juizo de admissibilidade","recurso extraordinario","recurso especial"]

def eh_merito(rec):
    classe=norm(rec.get("classe") or "")
    if any(x in classe for x in CLASSE_EXCLUI): return False
    if CLASSE_MERITO not in classe and classe!="":
        # classe presente mas nao é recurso inominado -> fora
        return False
    # checagem no conteúdo (cabeçalho) p/ pegar casos com classe vazia
    head=norm(rec.get("conteudo") or "")[:400]
    if any(x in head for x in CONTEUDO_EXCLUI): return False
    return True

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--max-por-frase",type=int,default=200)
    ap.add_argument("--out",default="aereo_limpo.jsonl")
    args=ap.parse_args()

    bruto=[]; total_reportado={}
    for a in FRASES:
        first=page(a,1); total_reportado[a]=first["itemCount"]
        got=0; p=1
        while got<args.max_por_frase:
            d=first if p==1 else page(a,p)
            decs=d.get("decisoes") or []
            if not decs: break
            for x in decs:
                bruto.append({
                    "numeroProcesso":x.get("numeroProcesso"),
                    "tipoDecisao":x.get("tipoDecisao"),
                    "classe":(x.get("classe") or {}).get("descricao"),
                    "orgaoJulgador":(x.get("orgaoJulgador") or {}).get("nome"),
                    "relator":(x.get("relator") or {}).get("nome"),
                    "dataJulgamento":x.get("dataJulgamento"),
                    "conteudo":x.get("conteudo") or "",
                    "_frase":a,
                })
                got+=1
                if got>=args.max_por_frase: break
            p+=1; time.sleep(0.25)
        print(f"  {a:24} reportado={first['itemCount']:6}  coletado={got}",file=sys.stderr)

    # --- FUNIL ---
    n_bruto=len(bruto)
    # dedup por processo
    seen={}; dedup=[]
    for r in bruto:
        pn=r["numeroProcesso"]
        if pn and pn not in seen:
            seen[pn]=1; dedup.append(r)
    n_dedup=len(dedup)
    # filtro de mérito
    limpo=[r for r in dedup if eh_merito(r)]
    n_limpo=len(limpo)

    with open(args.out,"w",encoding="utf-8") as fh:
        for r in limpo: fh.write(json.dumps(r,ensure_ascii=False)+"\n")

    from collections import Counter
    cls=Counter(norm(r.get("classe") or "(vazia)") for r in dedup)
    print("\n================= FUNIL DE LIMPEZA (tese AÉREO) =================",file=sys.stderr)
    print(f"  1) Coletado bruto ............... {n_bruto}",file=sys.stderr)
    print(f"  2) Após dedup por processo ...... {n_dedup}   (-{n_bruto-n_dedup} duplicados, {round(100*(n_bruto-n_dedup)/n_bruto)}%)",file=sys.stderr)
    print(f"  3) Após filtro de mérito ........ {n_limpo}   (-{n_dedup-n_limpo} não-mérito, {round(100*(n_dedup-n_limpo)/max(n_dedup,1))}%)",file=sys.stderr)
    print(f"  >> Corpus LIMPO p/ calcular % ... {n_limpo}  ({round(100*n_limpo/n_bruto)}% do bruto)",file=sys.stderr)
    print("\n  Classes encontradas (pós-dedup):",file=sys.stderr)
    for c,n in cls.most_common(8): print(f"     {n:4}  {c}",file=sys.stderr)
    print(f"\nOK -> {args.out}",file=sys.stderr)

if __name__=="__main__": main()
