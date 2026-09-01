#!/usr/bin/env python3
"""
Agrega todas as extrações (estruturado_*.jsonl) + o aéreo, normaliza num schema
único e calcula a jurimetria multidimensional (por tese, micro-tese, RÉU, turma,
relator) com intervalo de confiança de Wilson. Exporta juzia_base.json (consumido
pelo front) e imprime o relatório.
"""
import json, glob, math, os, statistics, sys
from collections import defaultdict, Counter

SCRATCH_AEREO="/private/tmp/claude-501/-Users-leandromelo-Desktop-Escrit-rio/0dd667bd-3a0f-49c3-9c75-e5c68c7bb01c/scratchpad/bagagem_estruturado.jsonl"

def wilson(k,n,z=1.96):
    if not n: return (0,0,0)
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d
    m=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (round(100*p), max(0,round(100*(c-m))), min(100,round(100*(c+m))))

FAV={"GANHOU","PARCIAL"}

import re
def parse_valor(v):
    if v is None: return None
    if isinstance(v,(int,float)): return float(v) if v else None
    s=str(v).strip()
    if not s: return None
    s=re.sub(r"[^0-9,\.]","",s)          # tira R$, espaços, texto
    if not s: return None
    if "," in s and "." in s:            # 2.000,00 -> 2000.00
        s=s.replace(".","").replace(",",".")
    elif "," in s:                        # 2000,00 -> 2000.00
        s=s.replace(",",".")
    try:
        f=float(s); return f if f>0 else None
    except: return None

REU_MAP={"TAM":"LATAM","TAM LINHAS AEREAS":"LATAM","LATAM AIRLINES":"LATAM",
         "GOL LINHAS AEREAS":"GOL","AZUL LINHAS AEREAS":"AZUL",
         "TRANSPORTES AEREOS PORTUGUESES":"TAP","BB":"BANCO DO BRASIL"}
def norm_reu(x):
    x=(x or "NAO IDENTIFICADO").strip().upper()
    return REU_MAP.get(x,x)

def norm_novo(r, foro="JUIZADO"):  # schema dos agentes
    return {
      "foro":foro,
      "ano":(r.get("dataJulgamento") or "")[:4],
      "numeroProcesso":r.get("numeroProcesso"),
      "tese_grupo":r.get("tese_grupo"),
      "micro_tese":r.get("micro_tese") or "OUTRO",
      "reu":norm_reu(r.get("reu")),
      "turma":r.get("orgaoJulgador"),
      "relator":r.get("relator"),
      "resultado":r.get("resultado_consumidor"),
      "dano_moral":bool(r.get("dano_moral_concedido")),
      "valor":parse_valor(r.get("dano_moral_valor")),
      "fundamentos":r.get("fundamentos") or [],
      "provas":r.get("prova_decisiva") or r.get("provas") or [],
      "comarca":r.get("comarca") or "", "vara":r.get("vara_origem") or "",
    }

def norm_aereo(r, foro="JUIZADO"):  # schema antigo do aéreo
    micro=r.get("tese_grupo")  # BAGAGEM / ATRASO / INSTITUICAO_FINANCEIRA
    grupo="AEREO" if micro in ("BAGAGEM","ATRASO") else "FINANCEIRO"
    return {
      "foro":foro,
      "ano":(r.get("dataJulgamento") or "")[:4],
      "numeroProcesso":r.get("numeroProcesso"),
      "tese_grupo":grupo,
      "micro_tese":("EXTRAVIO_AVARIA_BAGAGEM" if micro=="BAGAGEM"
                    else "ATRASO_MENOR_4H" if micro=="ATRASO" else "OUTRO"),
      "reu":norm_reu(r.get("re")),
      "turma":r.get("orgaoJulgador"),
      "relator":r.get("relator"),
      "resultado":r.get("resultado_consumidor"),
      "dano_moral":bool(r.get("dano_moral")),
      "valor":parse_valor(r.get("valor")),
      "fundamentos":r.get("fundamentos") or [],
      "provas":r.get("provas") or [],
      "comarca":"", "vara":"",
    }

def carregar():
    regs=[]
    for f in sorted(glob.glob("estruturado_*.jsonl")):
        foro = "JUSTICA_COMUM" if "comum" in f.lower() else "JUIZADO"
        for l in open(f,encoding="utf-8"):
            l=l.strip()
            if l: regs.append(norm_novo(json.loads(l), foro))
    if os.path.exists(SCRATCH_AEREO):
        for l in open(SCRATCH_AEREO,encoding="utf-8"):
            l=l.strip()
            if not l: continue
            rr=json.loads(l)
            if rr.get("tese_grupo")=="ATRASO": continue   # substituído por estruturado_atraso.jsonl
            regs.append(norm_aereo(rr))
    # dedup por processo
    seen={}; out=[]
    for r in regs:
        pn=r["numeroProcesso"]
        if pn and pn not in seen: seen[pn]=1; out.append(r)
    return out

def stat_grupo(regs):
    g=defaultdict(list)
    for r in regs: g[r["tese_grupo"]].append(r)
    setores=[]
    for grupo,rs in sorted(g.items(), key=lambda x:-len(x[1])):
        n=len(rs); fav=sum(1 for r in rs if r["resultado"] in FAV)
        p,lo,hi=wilson(fav,n)
        def por(campo,minn=1):
            d=defaultdict(list)
            for r in rs: d[r.get(campo) or "(n/d)"].append(r)
            res=[]
            for k,v in d.items():
                nn=len(v); ff=sum(1 for x in v if x["resultado"] in FAV)
                pp,l2,h2=wilson(ff,nn)
                if nn>=minn: res.append({"chave":k,"n":nn,"pct":pp,"ic":[l2,h2]})
            return sorted(res,key=lambda x:-x["n"])
        vals=[r["valor"] for r in rs if r["dano_moral"] and r["valor"]]
        dm=sum(1 for r in rs if r["dano_moral"])
        fund=Counter(f for r in rs for f in r["fundamentos"])
        prov=Counter(p for r in rs for p in r["provas"])
        forobk={}
        for fr in ("JUIZADO","JUSTICA_COMUM"):
            sub=[r for r in rs if r.get("foro")==fr]
            if sub:
                nf=len(sub); ff=sum(1 for x in sub if x["resultado"] in FAV)
                pf,l3,h3=wilson(ff,nf); forobk[fr]={"n":nf,"pct":pf,"ic":[l3,h3]}
        setores.append({
          "grupo":grupo,"n":n,"pct_exito":p,"ic":[lo,hi],
          "por_foro":forobk,
          "micro_teses":por("micro_tese"),
          "reus":por("reu"),
          "relatores":[x for x in por("relator",1)],
          "dano_moral":{"pct":round(100*dm/n) if n else 0,
                        "mediana":int(statistics.median(vals)) if vals else 0,
                        "min":int(min(vals)) if vals else 0,"max":int(max(vals)) if vals else 0},
          "fundamentos":[{"f":k,"freq":v} for k,v in fund.most_common(6)],
          "provas":[{"p":k,"freq":v} for k,v in prov.most_common(6)],
          "precedentes":[{"proc":r["numeroProcesso"],"turma":r["turma"],"relator":r["relator"],
                          "reu":r["reu"],"micro":r["micro_tese"],"resultado":r["resultado"],
                          "fund":(r["fundamentos"] or [""])[0],"prova":(r["provas"] or [""])[0],
                          "valor":r["valor"]} for r in rs],
        })
    return setores

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    regs=carregar()
    setores=stat_grupo(regs)
    base={"total":len(regs),"setores":setores}
    json.dump(base,open("juzia_base.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
    # registros nível-decisão (p/ filtro por ano/tese no dashboard)
    regj=[{"setor":r["tese_grupo"],"tese":r["micro_tese"],"ano":r["ano"] or None,"reu":r["reu"],
           "foro":r.get("foro"),"resultado":r["resultado"],
           "fav":1 if r["resultado"] in FAV else 0,"dm":1 if r["dano_moral"] else 0,
           "valor":r["valor"],"proc":r["numeroProcesso"]} for r in regs]
    json.dump(regj,open("registros_validados.json","w",encoding="utf-8"),ensure_ascii=False)
    # relatório
    print(f"=== BASE JUZIA: {len(regs)} decisões · {len(setores)} setores ===\n")
    for s in setores:
        print(f"■ {s['grupo']:12} n={s['n']:3}  êxito {s['pct_exito']}% IC[{s['ic'][0]}–{s['ic'][1]}]  "
              f"dano moral {s['dano_moral']['pct']}% (med R${s['dano_moral']['mediana']})")
        fb=s.get("por_foro",{})
        if fb: print("   foro:", " · ".join(f"{k} {v['pct']}%({v['n']})" for k,v in fb.items()))
        top_reu=[r for r in s['reus'] if r['n']>=2][:4]
        if top_reu:
            print("   por réu:", " · ".join(f"{r['chave']} {r['pct']}%({r['n']})" for r in top_reu))
    print("\nOK -> juzia_base.json")

if __name__=="__main__": main()
