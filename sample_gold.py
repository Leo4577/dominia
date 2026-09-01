#!/usr/bin/env python3
"""
Amostra ESTRATIFICADA por setor do corpus_50k para o GOLD SAMPLE (gabarito de calibração).
Escreve N arquivos de lote (gold_in_1.jsonl ...) com o inteiro teor completo, p/ validação.
Determinístico (seed fixa) → reproduzível.
"""
import json, random, sys
from collections import defaultdict
random.seed(42)
# quantos por setor (cobre a distribuição + garante mínimos p/ setores menores)
COTA={"FINANCEIRO":14,"FRAUDE":6,"AEREO":6,"SAUDE":5,"ECOMMERCE":4,"COELBA":4,"EMBASA":4,"TELECOM":4,"CONSUMO":3}
N_LOTES=int(sys.argv[1]) if len(sys.argv)>1 else 6

por_setor=defaultdict(list); vistos=set()
# prioriza corpus_50k (inteiro teor integral); completa setores menores com o corpus antigo
for fn in ["corpus_50k.jsonl","corpus_massa.jsonl"]:
    try: fh=open(fn,encoding="utf-8")
    except FileNotFoundError: continue
    for l in fh:
        r=json.loads(l); pn=r.get("numeroProcesso")
        if pn in vistos or not (r.get("conteudo") or "").strip(): continue
        vistos.add(pn); por_setor[r["setor"]].append(r)

amostra=[]
for setor,cota in COTA.items():
    pool=por_setor.get(setor,[])
    random.shuffle(pool)
    amostra.extend(pool[:cota])
random.shuffle(amostra)
print(f"amostra: {len(amostra)} acórdãos de {len(COTA)} setores",file=sys.stderr)

# distribui em lotes
lotes=[[] for _ in range(N_LOTES)]
for i,r in enumerate(amostra): lotes[i%N_LOTES].append(r)
for i,lote in enumerate(lotes,1):
    with open(f"gold_in_{i}.jsonl","w",encoding="utf-8") as fh:
        for r in lote:
            fh.write(json.dumps({"numeroProcesso":r["numeroProcesso"],"setor":r["setor"],
                "tese_busca":r.get("tese_busca"),"dataJulgamento":r.get("dataJulgamento"),
                "relator":r.get("relator"),"conteudo":r.get("conteudo")},ensure_ascii=False)+"\n")
    print(f"  gold_in_{i}.jsonl: {len(lote)} acórdãos",file=sys.stderr)

if __name__=="__main__": pass
