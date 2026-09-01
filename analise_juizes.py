#!/usr/bin/env python3
"""
Estatística POR JUIZ (Justiça Comum / Varas de Consumo, que têm inteiro teor).
% procedência × improcedência por juiz, a comarca dele, e dano moral mediano por tese/setor.
O Datajud não traz o juiz — por isso sai do TEXTO das sentenças. Saída: juizes_stats.json
"""
import json, statistics, os, re
from collections import defaultdict, Counter
from analise_dje import resultado, valor_cond, juiz_de, comarca_de, foro, norm

_TITULOS=re.compile(r"^(Presidente|Ju[ií]z[ao]?|Dr[a]?\.?|Exmo\.?|Exma\.?|Mm\.?|Meritíssim[ao]|Titular|Substitut[ao]|De Direito)\s+",re.I)
_LIXO=re.compile(r"\d|@|assinad|documento|certific|www|http",re.I)
def limpa_juiz(j):
    if not j: return None
    j=j.strip(" .,-")
    for _ in range(3): j=_TITULOS.sub("",j).strip()
    if _LIXO.search(j): return None
    partes=[p for p in j.split() if p]
    if len(partes)<2 or len(j)>48: return None      # precisa nome+sobrenome, sem frases
    return " ".join(partes)

def carregar(files):
    vis=set(); rows=[]
    for fn in files:
        if not os.path.exists(fn): continue
        for l in open(fn,encoding="utf-8"):
            try: r=json.loads(l)
            except Exception: continue
            pn=r.get("numeroProcesso")
            if pn and pn in vis: continue
            if pn: vis.add(pn)
            rows.append(r)
    return rows

def main():
    rows=carregar(["corpus_censo.jsonl","corpus_dje.jsonl"])
    J=defaultdict(lambda:{"proc":0,"improc":0,"dm":[],"com":Counter(),"tese":defaultdict(lambda:{"n":0,"proc":0,"dm":[]}),"ex":[]})
    for r in rows:
        t=r.get("conteudo") or ""
        j=limpa_juiz(juiz_de(t))
        if not j: continue
        res,venceu=resultado(t)
        if venceu is None: continue
        c=comarca_de(r.get("orgaoJulgador")); s=r.get("setor","CONSUMO"); v=valor_cond(t) if venceu else None
        d=J[j]
        if venceu: d["proc"]+=1
        else: d["improc"]+=1
        if c: d["com"][c]+=1
        if v: d["dm"].append(v)
        ts=d["tese"][s]; ts["n"]+=1
        if venceu: ts["proc"]+=1
        if v: ts["dm"].append(v)
        if len(d["ex"])<8 and r.get("numeroProcesso"): d["ex"].append(r["numeroProcesso"])
    def med(a): return int(statistics.median(a)) if a else None
    saida=[]
    for j,d in J.items():
        n=d["proc"]+d["improc"]
        if n<12: continue
        teses=sorted([{"setor":s,"n":v["n"],"pct":round(100*v["proc"]/v["n"]) if v["n"] else None,"dm":med(v["dm"])}
                      for s,v in d["tese"].items() if v["n"]>=4], key=lambda x:-x["n"])[:8]
        saida.append({"juiz":j,"n":n,"pct_proc":round(100*d["proc"]/n),"pct_improc":round(100*d["improc"]/n),
                      "comarca":(d["com"].most_common(1)[0][0] if d["com"] else None),
                      "dano_moral_mediana":med(d["dm"]),"por_tese":teses,"ex":d["ex"]})
    saida.sort(key=lambda x:-x["n"])
    # dano moral mediano por TESE/setor (geral, Justiça Comum)
    setor_dm=defaultdict(list)
    for r in rows:
        t=r.get("conteudo") or ""; res,venceu=resultado(t)
        if venceu:
            v=valor_cond(t)
            if v: setor_dm[r.get("setor","CONSUMO")].append(v)
    dm_tese=sorted([{"setor":s,"n":len(v),"mediana":med(v)} for s,v in setor_dm.items() if len(v)>=15],key=lambda x:-(x["mediana"] or 0))
    out={"fonte":"Sentenças de 1º grau (Varas de Consumo, DJEN) — juiz extraído do texto",
         "obs":"% de procedência entre decisões de mérito; comarca predominante do juiz; dano moral mediano. O Datajud (censo) não expõe o juiz.",
         "juizes":saida,"dano_moral_por_tese":dm_tese}
    json.dump(out,open("juizes_stats.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
    print(f"POR JUIZ: {len(saida)} juízes (n>=12)")
    for x in saida[:12]:
        print(f"  {x['juiz'][:34]:34} {x['comarca'] or '?':16} proc {x['pct_proc']}% improc {x['pct_improc']}% dm {x['dano_moral_mediana']} (n={x['n']})")
    print("dano moral mediano por tese:", [(t['setor'],t['mediana']) for t in dm_tese[:6]])

if __name__=="__main__": main()
