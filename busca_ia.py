#!/usr/bin/env python3
"""
MOTOR do "Modo IA" do SONDAJUS — busca ANCORADA em precedentes REAIS (anti-alucinação).
Recebe a descrição do caso em linguagem natural, procura na NOSSA base de acórdãos reais
(Turmas Recursais TJBA) e devolve os precedentes que EXISTEM, com nº de processo + ementa.
Versão free (léxico + expansão de sinônimos). A versão semântica plena usa embeddings (ver nota).

Uso: python3 busca_ia.py "atraso de voo com perda de conexão"
"""
import json, re, sys, unicodedata, heapq
from collections import Counter

def norm(s): return unicodedata.normalize("NFKD",(s or "").lower()).encode("ascii","ignore").decode()
# expansão de sinônimos (o que a busca por palavra não pega, aqui a gente ensina)
SIN={"voo":["aereo","aeronave","companhia aerea","aereas"],"atraso":["atrasado","demora","cancelamento"],
     "bagagem":["mala","extravio","volume"],"negativacao":["inscricao indevida","spc","serasa","cadastro de inadimplente"],
     "consignado":["emprestimo","desconto em beneficio","rmc","margem consignavel"],"maconha":["cannabis","entorpecente"],
     "plano de saude":["operadora","cobertura","ans","carencia"],"golpe":["fraude","estelionato","pix","engenharia social"],
     "energia":["coelba","fatura","medidor"],"agua":["embasa","esgoto"],"dano moral":["indenizacao","reparacao"]}
STOP=set("de da do das dos a o e em para por com que se um uma no na nos nas ao aos".split())

def termos(q):
    base=[t for t in re.findall(r"[a-z]+",norm(q)) if t not in STOP and len(t)>2]
    exp=set(base)
    ql=norm(q)
    for k,vs in SIN.items():
        if k in ql or any(t in k for t in base):
            exp.update(norm(v) for v in vs); exp.update(k.split())
    return list(exp)

def ementa(t):
    m=re.search(r"EMENTA(.{80,900}?)(ACORD|VISTOS|RELAT|\.\s*[A-Z]{4,}\s)",t,re.S|re.I)
    frag=(m.group(1) if m else t[:600])
    return re.sub(r"\s+"," ",frag).strip()[:600]

def main():
    if len(sys.argv)<2: print('uso: busca_ia.py "descreva o caso"'); return
    q=sys.argv[1]; ts=termos(q)
    print("caso: {}\ntermos (com sinônimos): {}\n".format(q,", ".join(sorted(ts))),file=sys.stderr)
    top=[]  # heap de (score, i, registro)
    for i,l in enumerate(open("corpus_50k.jsonl",encoding="utf-8")):
        r=json.loads(l); t=norm(r.get("conteudo") or "")
        if not t: continue
        score=sum(t.count(term) for term in ts)
        if score<=2: continue
        # bônus se vários termos distintos aparecem (relevância, não só frequência)
        distintos=sum(1 for term in ts if term in t)
        score=score+distintos*5
        if len(top)<8: heapq.heappush(top,(score,i,r))
        elif score>top[0][0]: heapq.heapreplace(top,(score,i,r))
    res=sorted(top,reverse=True)
    print("=== {} precedentes REAIS encontrados ===".format(len(res)))
    for score,i,r in res[:5]:
        print("\n• Processo {} | {} | {}".format(r.get("numeroProcesso"),r.get("orgaoJulgador") or "Turma Recursal",(r.get("dataJulgamento") or "")[:10]))
        print("  ementa:",ementa(r.get("conteudo") or "")[:280],"...")

if __name__=="__main__": main()
