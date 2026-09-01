#!/usr/bin/env python3
"""
Análise das SENTENÇAS de 1º grau (corpus_dje.jsonl) — gera os rankings estilo AeroJuris, melhor:
  - dano moral por ÁREA (setor): onde o dano moral é maior
  - ranking de COMARCAS (n, % procedência, dano moral mediano)
  - CIDADES analisadas (contagem), JUÍZES mapeados (ranking), RÉUS (ranking)
Sentença de 1º grau tem dispositivo claro (JULGO (IM)PROCEDENTE) -> sinal mais confiável.
Saída: dje_stats.json
"""
import json, re, unicodedata, statistics, sys, os
from collections import defaultdict, Counter
from analise_heuristica import REUS_C, valor_dm

def norm(s): return unicodedata.normalize("NFKD",s or "").encode("ascii","ignore").decode()

RE_PROC=re.compile(r"JULGO\s+(?:TOTALMENTE\s+)?PROCEDENTE", re.I)
RE_PARC=re.compile(r"JULGO\s+(?:O[S]?\s+PEDIDO[S]?\s+)?PARCIALMENTE\s+PROCEDENTE", re.I)
RE_IMPR=re.compile(r"JULGO\s+IMPROCEDENTE|IMPROCEDENTE[S]?\s+O[S]?\s+PEDIDO|JULGO\s+EXTINTO", re.I)
def resultado(t):
    tn=norm(t)
    if RE_PARC.search(tn): return "PARCIAL", True
    if RE_PROC.search(tn): return "PROCEDENTE", True
    if RE_IMPR.search(tn): return "IMPROCEDENTE", False
    # fallback por marcadores
    if re.search(r"CONDENO A (RE|PARTE RE|ACIONAD)", tn, re.I): return "PROCEDENTE", True
    return "INDEF", None

RE_JUIZ=re.compile(r"([A-ZÁÂÃÉÊÍÓÔÕÚÇ][A-ZÁÂÃÉÊÍÓÔÕÚÇ\.\s]{6,55}?)\s+JU[ÍI]Z[A]?\s+DE\s+DIREITO")
def juiz_de(texto):
    if not texto: return None
    for m in list(RE_JUIZ.finditer(texto[-1500:]))[::-1] or RE_JUIZ.finditer(texto):
        nome=re.sub(r"\s+"," ",m.group(1)).strip()
        nome=re.sub(r"^(O|A|E|DR|DRA|JUIZ|JUIZA)\b\.?\s*","",nome,flags=re.I).strip().title()
        if 8<=len(nome)<=55 and " " in nome: return nome
    return None

def acha_reu(cab):
    for rx,nome in REUS_C:
        if rx.search(cab): return nome
    return None
# valor de dano moral ancorado na CONDENAÇÃO (última ocorrência = dispositivo), não no pedido
RE_COND=re.compile(r"dano[s]?\s+mora[li][s]?[^.]{0,60}?(?:fix|arbitr|condeno|no valor de|no montante de|em)[^R\$]{0,25}?R\$\s?([\d\.]+,\d{2})", re.I)
def valor_cond(t):
    ms=list(RE_COND.finditer(t or ""))
    if not ms: return None
    try:
        v=float(ms[-1].group(1).replace(".","").replace(",",".")); return v if 200<=v<=100000 else None
    except: return None
# âncoras que antecedem o nome da comarca/cidade (a cidade fica no fim do nome do órgão)
ANCORAS=["COMARCA DE ","COMERCIAIS DE ","COMERCIAS DE ","CONSUMO DE ","CIVEIS DE ","CÍVEIS DE ",
         "TRAB. DE ","TRAB DE ","TRABALHO DE ","FAMILIA DE ","FAMÍLIA DE ","SUCESSOES DE ","FEITOS DE "]
def foro(orgao):
    o=(orgao or "").upper()
    if "JUIZADO" in o or "SISTEMA DOS JUIZADOS" in o: return "JUIZADO_ESPECIAL"
    if ("REL" in o and "CONS" in o): return "VARA_CONSUMO"
    if "CIVEL" in norm(o) or "CIVEIS" in norm(o): return "VARA_CIVEL"
    return "OUTRO_1G"
RUIDO=re.compile(r"CONSUMO|RELA|FEITOS|C[IÍ]VE|COMERC|VARA|FAZENDA|TRAB|SUCESS|FAMIL|JUIZADO|TURMA|COMARCA|REG\.|P[UÚ]BLIC|ACIDENTE")
ALIAS={"Capital":"Salvador","Salvador Capital":"Salvador"}
def _tc(c):
    CONN={"DE","DA","DO","DAS","DOS","E"}
    r=" ".join(w.lower() if w in CONN else w.capitalize() for w in c.split())
    return ALIAS.get(r,r)
def comarca_de(orgao):
    o=re.sub(r"\s+"," ",(orgao or "").upper()).strip()
    if not o: return None
    # formato "CIDADE > VARA..." (cidade no começo)
    if ">" in o:
        cand=o.split(">")[0].strip(" .,-")
        if 3<=len(cand)<=40 and not RUIDO.search(cand): return _tc(cand)
    # formato "...VARA ... DE CIDADE" (cidade no fim, após âncora)
    pos=-1; anc=""
    for a in ANCORAS:
        i=o.rfind(a)
        if i>pos: pos=i; anc=a
    if pos<0: return None
    c=re.sub(r"\s+"," ",o[pos+len(anc):].strip(" .,-"))
    if not c or len(c)<3 or len(c)>40 or RUIDO.search(c): return None
    return _tc(c)

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

def foro_grupo(orgao):
    return "JUIZADO" if foro(orgao)=="JUIZADO_ESPECIAL" else "COMUM"

def main():
    rows=carregar(["corpus_censo.jsonl","corpus_dje.jsonl","corpus_projudi.jsonl"])
    G=["JUIZADO","COMUM"]
    setor_res={g:defaultdict(lambda:[0,0]) for g in G}
    setor_dm ={g:defaultdict(list) for g in G}
    comarca  ={g:defaultdict(lambda:{"n":0,"proc":0,"dm":[]}) for g in G}
    reu      ={g:defaultdict(lambda:{"n":0,"proc":0,"dm":[]}) for g in G}
    cross    ={g:defaultdict(lambda:defaultdict(lambda:{"n":0,"proc":0,"dm":[]})) for g in G}
    juizes=Counter(); cidades=set(); foros=Counter(); registros=[]
    for r in rows:
        t=r.get("conteudo") or ""; s=r["setor"]
        res,venceu=resultado(t); v=valor_cond(t)
        rr=acha_reu(norm(t[:1500]).upper())
        c=comarca_de(r.get("orgaoJulgador"))
        j=juiz_de(t) or r.get("juiz")
        ft=foro(r.get("orgaoJulgador")); g="JUIZADO" if ft=="JUIZADO_ESPECIAL" else "COMUM"
        foros[ft]+=1
        registros.append({"proc":r["numeroProcesso"],"s":s,"c":c,"j":j,"r":rr,"fg":g,
                          "res":res,"v":v if venceu else None,"d":(r.get("dataJulgamento") or "")[:10],
                          "link":r.get("link"),"tese":r.get("tese_busca")})
        if j: juizes[j]+=1
        if c: cidades.add(c)
        if venceu is not None:
            setor_res[g][s][0]+=1
            if venceu: setor_res[g][s][1]+=1
        if v and venceu: setor_dm[g][s].append(v)
        if c:
            for D in (comarca[g][c], cross[g][s][c]):
                D["n"]+=1
                if venceu: D["proc"]+=1
                if v and venceu: D["dm"].append(v)
        if rr:
            reu[g][rr]["n"]+=1
            if venceu: reu[g][rr]["proc"]+=1
            if v and venceu: reu[g][rr]["dm"].append(v)

    def med(a): return int(statistics.median(a)) if a else None
    def por_foro(g):
        sr,sdm=setor_res[g],setor_dm[g]
        dm_area=sorted([{"setor":s,"n_dm":len(sdm[s]),"mediana":med(sdm[s]),
                         "pct_dm":round(100*len(sdm[s])/sr[s][0]) if sr[s][0] else None}
                        for s in sr if sr[s][0]>=20 and sdm[s]], key=lambda x:-(x["mediana"] or 0))
        exito=sorted([{"setor":s,"n":d[0],"pct":round(100*d[1]/d[0]) if d[0] else None} for s,d in sr.items() if d[0]>=20],
                     key=lambda x:-(x["pct"] or 0))
        coms=sorted([{"comarca":c,"n":d["n"],"pct":round(100*d["proc"]/d["n"]) if d["n"] else None,
                      "dm":med(d["dm"]) if len(d["dm"])>=15 else None,"pct_dm":round(100*len(d["dm"])/d["n"]) if d["n"] else None}
                     for c,d in comarca[g].items() if d["n"]>=8], key=lambda x:-x["n"])[:40]
        rs=sorted([{"reu":c,"n":d["n"],"pct":round(100*d["proc"]/d["n"]) if d["n"] else None,
                    "dm":med(d["dm"]) if len(d["dm"])>=10 else None}
                   for c,d in reu[g].items() if d["n"]>=5], key=lambda x:-x["n"])[:20]
        comp={}
        for s in cross[g]:
            lst=[{"comarca":c,"n":d["n"],"pct":round(100*d["proc"]/d["n"]) if d["n"] else None,
                  "dm":med(d["dm"]) if len(d["dm"])>=8 else None,"pct_dm":round(100*len(d["dm"])/d["n"]) if d["n"] else None}
                 for c,d in cross[g][s].items() if d["n"]>=8]
            if lst: comp[s]=sorted(lst,key=lambda x:-x["n"])[:25]
        return {"total":sum(d[0] for d in sr.values()),"dano_moral_por_area":dm_area,
                "exito_por_area":exito,"comarcas":coms,"reus":rs,"comparador":comp}

    out={"total":len(rows),"cidades":len(cidades),"n_juizes":len(juizes),"foros":dict(foros),
         "juizes":[{"juiz":j,"n":n} for j,n in juizes.most_common(40)],
         "por_foro":{g:por_foro(g) for g in G}}
    json.dump(out,open("dje_stats.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
    registros.sort(key=lambda x:x.get("d") or "", reverse=True)   # recentes primeiro (p/ embed capado)
    json.dump(registros,open("registros_dje.json","w",encoding="utf-8"),ensure_ascii=False)
    print(f"1º grau: {len(rows)} sentenças · {len(cidades)} cidades · {len(juizes)} juízes")
    print("foros:",dict(foros))
    for g in G:
        pf=out["por_foro"][g]
        print(f"\n== {g} (n={pf['total']}) ==")
        for a in pf["dano_moral_por_area"][:5]:
            print(f"  {a['setor']:11} dano moral med R$ {a['mediana']} · deferido em {a['pct_dm']}% dos casos (n_dm={a['n_dm']})")

if __name__=="__main__": main()
