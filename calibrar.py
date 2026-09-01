#!/usr/bin/env python3
"""
CALIBRAÇÃO — mede a assertividade de um modelo barato (Haiku) contra o GABARITO humano-assistido
(gold_sample.jsonl). Roda os MESMOS 50 acórdãos pelo modelo e compara o campo que importa:
consumidor_venceu (base do % de êxito), resultado, dano moral e valor.

Subcomandos:
  merge                      junta gold_out_*.jsonl -> gold_sample.jsonl (o gabarito)
  extrair [MODEL]            roda os 50 do gold pelo modelo (default haiku) -> gold_<model>.jsonl  (PRECISA de API key; ~R$1)
  comparar gold_<model>.jsonl   compara com o gabarito e imprime a acurácia

Se a concordância em 'consumidor_venceu' for >90%, o Haiku serve p/ os 50k (Batch, ~R$1.150).
"""
import os, sys, json, glob

GOLD="gold_sample.jsonl"
SCHEMA={"type":"object","additionalProperties":False,"required":["consumidor_venceu","resultado","dano_moral_deferido","valor_dano_moral","reu"],
 "properties":{
  "consumidor_venceu":{"type":["boolean","null"]},
  "resultado":{"type":"string","enum":["PROCEDENTE","PARCIALMENTE_PROCEDENTE","IMPROCEDENTE","EXTINTO_SEM_MERITO","INDETERMINADO"]},
  "micro_tese":{"type":"string"},
  "fundamentos_determinantes":{"type":"array","items":{"type":"string"}},
  "provas_decisivas":{"type":"array","items":{"type":"string"}},
  "dano_moral_deferido":{"type":"boolean"},
  "valor_dano_moral":{"type":["number","null"]},
  "reu":{"type":["string","null"]}}}
SYSTEM=("Você é advogado especialista em Juizados/Turmas Recursais. Extraia o resultado jurimétrico do acórdão. "
 "REGRA CRÍTICA: 'consumidor_venceu' mede o ÊXITO DO CONSUMIDOR NO MÉRITO, não quem ganhou o recurso. "
 "Se a EMPRESA recorreu e o recurso foi improvido mantendo condenação → true. Se o CONSUMIDOR recorreu e foi provido "
 "reformando improcedência → true. Qualquer procedência (mesmo parcial) → true, PARCIALMENTE_PROCEDENTE. "
 "Improcedência total / recurso do consumidor improvido → false. Extinto sem mérito ou indeterminável → null. "
 "Seja conservador; dano_moral_deferido só se arbitrado a favor do consumidor.")

def merge():
    seen=set(); n=0
    with open(GOLD,"w",encoding="utf-8") as out:
        for fn in sorted(glob.glob("gold_out_*.jsonl")):
            for l in open(fn,encoding="utf-8"):
                l=l.strip()
                if not l: continue
                try: r=json.loads(l)
                except Exception: continue
                pn=r.get("numeroProcesso")
                if pn in seen: continue
                seen.add(pn); out.write(json.dumps(r,ensure_ascii=False)+"\n"); n+=1
    print(f"gabarito: {n} acórdãos -> {GOLD}",file=sys.stderr)

def extrair(model):
    import anthropic
    client=anthropic.Anthropic()
    # casa o gold (numeroProcesso) com o inteiro teor dos corpora
    teor={}
    for fn in ["corpus_50k.jsonl","corpus_massa.jsonl"]:
        if not os.path.exists(fn): continue
        for l in open(fn,encoding="utf-8"):
            r=json.loads(l); teor.setdefault(r["numeroProcesso"],r.get("conteudo") or "")
    gold=[json.loads(l) for l in open(GOLD,encoding="utf-8")]
    outfn=f"gold_{model.split('-')[1] if '-' in model else model}.jsonl"
    with open(outfn,"w",encoding="utf-8") as out:
        for i,g in enumerate(gold,1):
            pn=g["numeroProcesso"]; c=teor.get(pn,"")[:16000]
            m=client.messages.create(model=model,max_tokens=1400,system=SYSTEM,
                output_config={"format":{"type":"json_schema","schema":SCHEMA}},
                messages=[{"role":"user","content":f"Acórdão:\n\n{c}"}])
            txt=next(x.text for x in m.content if x.type=="text")
            d=json.loads(txt); d["numeroProcesso"]=pn; d["setor"]=g["setor"]
            out.write(json.dumps(d,ensure_ascii=False)+"\n")
            print(f"  {i}/{len(gold)} {pn}",file=sys.stderr)
    print(f"-> {outfn}",file=sys.stderr)

def comparar(candfn):
    gold={json.loads(l)["numeroProcesso"]:json.loads(l) for l in open(GOLD,encoding="utf-8")}
    cand={json.loads(l)["numeroProcesso"]:json.loads(l) for l in open(candfn,encoding="utf-8")}
    pares=[(gold[k],cand[k]) for k in gold if k in cand]
    n=len(pares)
    if not n: print("sem pares p/ comparar"); return
    acc_venceu=sum(1 for g,c in pares if g.get("consumidor_venceu")==c.get("consumidor_venceu"))
    acc_res=sum(1 for g,c in pares if g.get("resultado")==c.get("resultado"))
    acc_dm=sum(1 for g,c in pares if bool(g.get("dano_moral_deferido"))==bool(c.get("dano_moral_deferido")))
    # valor: erro relativo médio onde ambos têm valor
    vpairs=[(g["valor_dano_moral"],c.get("valor_dano_moral")) for g,c in pares if g.get("valor_dano_moral") and c.get("valor_dano_moral")]
    err=sum(abs(a-b)/a for a,b in vpairs)/len(vpairs) if vpairs else None
    print(f"\n=== CALIBRAÇÃO ({n} acórdãos) ===")
    print(f"consumidor_venceu : {100*acc_venceu//n}%  ({acc_venceu}/{n})   <-- métrica que sustenta o % de êxito")
    print(f"resultado (5 cat) : {100*acc_res//n}%  ({acc_res}/{n})")
    print(f"dano moral (s/n)  : {100*acc_dm//n}%  ({acc_dm}/{n})")
    if err is not None: print(f"valor dano moral  : erro médio {round(100*err)}% (n={len(vpairs)})")
    print(f"\nVEREDITO: Haiku {'SERVE p/ os 50k (>=90%)' if 100*acc_venceu//n>=90 else 'precisa de Sonnet ou revisão do prompt (<90%)'}")
    # lista divergências p/ inspeção
    div=[(g['numeroProcesso'],g.get('consumidor_venceu'),c.get('consumidor_venceu')) for g,c in pares if g.get('consumidor_venceu')!=c.get('consumidor_venceu')]
    if div:
        print("\ndivergências em consumidor_venceu (proc / gabarito / modelo):")
        for p,a,b in div: print(f"  {p}  {a} != {b}")

def main():
    if len(sys.argv)<2: print(__doc__); return
    cmd=sys.argv[1]
    if cmd=="merge": merge()
    elif cmd=="extrair": extrair(sys.argv[2] if len(sys.argv)>2 else "claude-haiku-4-5")
    elif cmd=="comparar": comparar(sys.argv[2])
    else: print(__doc__)

if __name__=="__main__": main()
