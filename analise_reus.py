#!/usr/bin/env python3
"""
(B) RANKING POR RÉU dos acórdãos das Turmas Recursais da BA (o 2º grau do Juizado).
De onde vem o réu, o dano moral e o "quem ganha contra quem" — o Datajud não tem partes,
mas o TEXTO do acórdão tem. Sinal de êxito (FAV/UNFAV), dano moral (condenação), comarca de
origem e AMOSTRA DE PROCESSOS pra validação humana. Saída: reus_stats.json
"""
import json, re, statistics, unicodedata, os
from collections import defaultdict
from analise_heuristica import sinal, REUS_C
from analise_dje import valor_cond

def norm(s): return unicodedata.normalize("NFKD",(s or "")).encode("ascii","ignore").decode()
def acha_reu(t):
    u=norm(t[:2500]).upper()
    for rx,nome in REUS_C:
        if rx.search(u): return nome
    return None
RE_COM=re.compile(r"COMARCA DE ([A-ZÁÂÃÉÊÍÓÔÕÚÇ' ]{3,30}?)(?=\s*(?:[/\-–,.\n]|VARA|JUIZ|-|$))", re.I)
def comarca_de(t):
    m=RE_COM.search(t or "")
    return re.sub(r"\s+"," ",m.group(1)).strip().title() if m else None
SETOR={"LATAM":"AEREO","GOL":"AEREO","AZUL":"AEREO","TAP":"AEREO","AVIANCA":"AEREO","IBERIA":"AEREO","AMERICAN":"AEREO",
       "COELBA":"COELBA","EMBASA":"EMBASA","VIVO":"TELECOM","CLARO":"TELECOM","TIM":"TELECOM","OI":"TELECOM"}

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
    rows=carregar(["corpus_50k.jsonl","corpus_massa.jsonl"])
    reu=defaultdict(lambda:{"n":0,"fav":0,"dm":[],"ex_fav":[],"ex_unf":[],"com":defaultdict(lambda:[0,0])})
    for r in rows:
        t=r.get("conteudo") or ""; rr=acha_reu(t)
        if not rr: continue
        sg=sinal(t); v=valor_cond(t); c=comarca_de(t); pn=r.get("numeroProcesso")
        d=reu[rr]; d["n"]+=1
        venceu = sg=="FAV"
        if venceu:
            d["fav"]+=1
            if v: d["dm"].append(v)
            if len(d["ex_fav"])<8 and pn: d["ex_fav"].append(pn)
        elif sg=="UNFAV" and len(d["ex_unf"])<8 and pn: d["ex_unf"].append(pn)
        if c:
            cc=d["com"][c]; cc[0]+=1
            if venceu: cc[1]+=1
    saida=[]
    for nome,d in reu.items():
        dec=d["n"]
        if dec<8: continue
        comarcas=sorted([{"comarca":c,"n":v[0],"pct":round(100*v[1]/v[0]) if v[0] else None}
                         for c,v in d["com"].items() if v[0]>=5], key=lambda x:-x["n"])[:12]
        saida.append({"reu":nome,"setor":SETOR.get(nome,"FINANCEIRO"),"n":dec,
            "pct_fav_sinal":round(100*d["fav"]/dec),
            "dano_moral_mediana":int(statistics.median(d["dm"])) if d["dm"] else None,
            "n_dm":len(d["dm"]),"ex_favoravel":d["ex_fav"],"ex_desfavoravel":d["ex_unf"],
            "por_comarca":comarcas})
    saida.sort(key=lambda x:-x["n"])
    out={"fonte":"Acórdãos das Turmas Recursais TJBA (2º grau do Juizado)","metodo":"sinal heurístico FAV/UNFAV",
         "obs":"% de êxito é SINAL (não validado por IA); use os nº de processo p/ validar. Dano moral = condenação no texto.",
         "reus":saida}
    json.dump(out,open("reus_stats.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
    print("RÉUS: {} réus (n>=8)".format(len(saida)))
    for x in saida[:14]:
        print("  {:16} n={:5} êxito {}%  dano moral {}  ex_fav={}".format(
            x["reu"],x["n"],x["pct_fav_sinal"],("R$ "+str(x["dano_moral_mediana"])) if x["dano_moral_mediana"] else "—",x["ex_favoravel"][:1]))

if __name__=="__main__": main()
