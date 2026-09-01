#!/usr/bin/env python3
"""
Extrator em LOTE (Batch API da Anthropic) — a ferramenta para VALIDAR EM ESCALA (50k+).
50% mais barato que chamadas normais, assíncrono (até 100k requisições por lote).
Lê um corpus (numeroProcesso, setor, conteudo) e extrai o schema estruturado por setor.

Pré-requisito:
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...

Uso:
    # 1) submete (cria os lotes e salva os IDs em lotes_ids.json)
    python3 extrator_lote.py submeter corpus_massa.jsonl --limite 50000
    # 2) coleta quando prontos (pode rodar várias vezes; é idempotente)
    python3 extrator_lote.py coletar --out estruturado_lote.jsonl

Modelo (custo): MODEL=claude-haiku-4-5 (mais barato) | claude-sonnet-5 (equilíbrio)
"""
import os, sys, json, argparse, time
import anthropic
from teses_config import config, GRUPOS

MODEL=os.environ.get("MODEL","claude-haiku-4-5")
# mapeia setor do corpus -> grupo do teses_config (fallback: FINANCEIRO genérico)
MAPA={"FINANCEIRO":"FINANCEIRO","AEREO":"AEREO","SAUDE":"SAUDE","COELBA":"COELBA","EMBASA":"EMBASA",
      "TELECOM":"TELECOM" if "TELECOM" in GRUPOS else "FINANCEIRO",
      "ECOMMERCE":"ECOMMERCE" if "ECOMMERCE" in GRUPOS else "FINANCEIRO",
      "FRAUDE":"FINANCEIRO","CONSUMO":"FINANCEIRO","APOSTAS":"FINANCEIRO"}

def cfg(setor):
    g=MAPA.get(setor,"FINANCEIRO")
    if g not in GRUPOS: g="FINANCEIRO"
    return config(g)

def submeter(infile, limite):
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request
    client=anthropic.Anthropic()
    rows=[json.loads(l) for l in open(infile,encoding="utf-8")][:limite]
    # agrupa por setor (cada requisição carrega o schema/prompt do seu setor)
    reqs=[]
    for i,r in enumerate(rows):
        c=cfg(r.get("setor","FINANCEIRO"))
        reqs.append(Request(custom_id=f"{i}::{r.get('numeroProcesso','')}",
            params=MessageCreateParamsNonStreaming(model=MODEL,max_tokens=1400,system=c["system"],
                output_config={"format":{"type":"json_schema","schema":c["schema"]}},
                messages=[{"role":"user","content":f"Extraia os dados deste acórdão:\n\n{(r.get('conteudo') or '')[:16000]}"}])))
    # a Batch API aceita até 100k por lote; fatiamos em blocos de 40k por segurança
    ids=[]
    for k in range(0,len(reqs),40000):
        b=client.messages.batches.create(requests=reqs[k:k+40000])
        ids.append(b.id); print(f"lote {b.id}: {min(40000,len(reqs)-k)} requisições",file=sys.stderr)
    json.dump({"model":MODEL,"ids":ids,"infile":infile},open("lotes_ids.json","w"))
    print(f"OK: {len(reqs)} decisões em {len(ids)} lote(s). IDs salvos em lotes_ids.json. Rode 'coletar' depois.",file=sys.stderr)

def coletar(out):
    client=anthropic.Anthropic()
    meta=json.load(open("lotes_ids.json"))
    fh=open(out,"w",encoding="utf-8"); ok=0; pend=0
    for bid in meta["ids"]:
        b=client.messages.batches.retrieve(bid)
        if b.processing_status!="ended":
            print(f"lote {bid}: {b.processing_status} ({b.request_counts})",file=sys.stderr); pend+=1; continue
        for res in client.messages.batches.results(bid):
            if res.result.type!="succeeded": continue
            try:
                txt=next(x.text for x in res.result.message.content if x.type=="text")
                dados=json.loads(txt)
            except Exception: continue
            np=res.custom_id.split("::",1)[-1]
            fh.write(json.dumps({"numeroProcesso":np,**dados,"modelo_extrator":meta["model"]},ensure_ascii=False)+"\n"); ok+=1
    fh.close()
    if pend: print(f"\n{pend} lote(s) ainda processando — rode 'coletar' de novo mais tarde.",file=sys.stderr)
    print(f"{ok} decisões validadas -> {out}",file=sys.stderr)

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    s=sub.add_parser("submeter"); s.add_argument("infile"); s.add_argument("--limite",type=int,default=50000)
    c=sub.add_parser("coletar"); c.add_argument("--out",default="estruturado_lote.jsonl")
    a=ap.parse_args()
    if a.cmd=="submeter": submeter(a.infile,a.limite)
    else: coletar(a.out)

if __name__=="__main__": main()
