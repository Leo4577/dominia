#!/usr/bin/env python3
"""
Índice compacto p/ a aba "Busca por caso" (client-side, anti-alucinação).
Extrai de cada acórdão real: nº processo, órgão, data, réu, resultado, ementa curta + termos.
Amostra diversa (cap p/ manter o site leve). Saída: busca_index.json
"""
import json, re, unicodedata
from collections import Counter
from analise_heuristica import sinal, REUS_C
POR_FONTE=2200; EMENTA_MAX=190   # amostra de cada grau
# (arquivo, grau) — Turmas Recursais (2º grau do Juizado) + Varas de Consumo (1º grau)
FONTES=[("corpus_50k.jsonl","TR"),("corpus_censo.jsonl","1G")]
def norm(s): return unicodedata.normalize("NFKD",(s or "").lower()).encode("ascii","ignore").decode()
def reu(t):
    u=norm(t[:2500]).upper()
    for rx,nome in REUS_C:
        if rx.search(u): return nome
    return None
def ementa(t):
    m=re.search(r"EMENTA(.{60,700}?)(ACORD|VISTOS|RELAT|\bDECIDO\b)",t,re.S|re.I)
    if not m: m=re.search(r"(JULGO[^.]{20,400}\.)",t,re.I)   # 1º grau: pega o dispositivo
    frag=(m.group(1) if m else t[:400])
    return re.sub(r"\s+"," ",frag).strip()[:EMENTA_MAX]
STOP=set("de da do das dos a o e em para por com que se um uma no na tribunal justica estado bahia poder judiciario recurso".split())
def termos(t):
    c=Counter(w for w in re.findall(r"[a-z]{4,}",norm(t)[:4000]) if w not in STOP)
    return " ".join(w for w,_ in c.most_common(30))
def main():
    import os
    seen=set(); out=[]
    for fn,grau in FONTES:
        if not os.path.exists(fn): continue
        n=0
        for l in open(fn,encoding="utf-8"):
            r=json.loads(l); t=r.get("conteudo") or ""; pn=r.get("numeroProcesso")
            if not t or pn in seen: continue
            seen.add(pn); sg=sinal(t)
            out.append({"p":pn,"g":grau,"o":(r.get("orgaoJulgador") or ("Turma Recursal" if grau=="TR" else "1º grau"))[:36],
                        "d":(r.get("dataJulgamento") or "")[:10],"r":reu(t),
                        "res":"favorável" if sg=="FAV" else("desfavorável" if sg=="UNFAV" else "—"),
                        "e":ementa(t),"k":termos(t)})
            n+=1
            if n>=POR_FONTE: break
    json.dump({"n":len(out),"itens":out},open("busca_index.json","w",encoding="utf-8"),ensure_ascii=False)
    tr=sum(1 for x in out if x["g"]=="TR"); g1=sum(1 for x in out if x["g"]=="1G")
    print(f"índice de busca: {len(out)} decisões ({tr} Turmas + {g1} 1º grau) -> busca_index.json")

if __name__=="__main__": main()
