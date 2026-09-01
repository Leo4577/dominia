#!/usr/bin/env python3
"""
Pipeline validado JUZIA — tese AÉREO (passos 2-4)
Le o corpus LIMPO (aereo_limpo.jsonl) e produz percentuais AUDITÁVEIS.

  2) Extração estruturada por IA (structured output)
  3) Validação IA-valida-IA: 2 modelos extraem; onde CONCORDAM = alta confiança
  4) Agregação com intervalo de confiança de Wilson (nunca % solto sem n)

Uso:
    export ANTHROPIC_API_KEY=sk-ant-...
    python3 pipeline_aereo.py aereo_limpo.jsonl --limit 200
Modelos (ajustáveis):
    MODEL_A (extrator de volume)  padrão claude-sonnet-5
    MODEL_B (auditor)             padrão claude-opus-5
"""
import os, json, sys, argparse, math, time, statistics
import anthropic
from collections import Counter, defaultdict

MODEL_A = os.environ.get("MODEL_A", "claude-sonnet-5")
MODEL_B = os.environ.get("MODEL_B", "claude-opus-5")

SCHEMA = {
  "type":"object","additionalProperties":False,
  "properties":{
    "e_merito_aereo":{"type":"boolean","description":"É decisão de mérito sobre transporte aéreo/bagagem? (false p/ descartar)"},
    "micro_tese":{"type":"string","enum":[
        "EXTRAVIO_DEFINITIVO","EXTRAVIO_TEMPORARIO","BAGAGEM_DANIFICADA",
        "ATRASO_MAIOR_4H","ATRASO_MENOR_4H","CANCELAMENTO_VOO","OVERBOOKING","OUTRO"]},
    "resultado_consumidor":{"type":"string","enum":["GANHOU","PARCIAL","PERDEU","NAO_APLICA"],
        "description":"Resultado final sob a ótica do consumidor (autor)."},
    "dano_moral_concedido":{"type":"boolean"},
    "dano_moral_valor_reais":{"type":"number","description":"Valor do dano moral em reais; 0 se não concedido"},
    "dano_material_concedido":{"type":"boolean"},
    "fundamentos":{"type":"array","items":{"type":"string"},"description":"1-4 fundamentos determinantes"},
    "prova_decisiva":{"type":"array","items":{"type":"string"}},
    "comarca":{"type":"string"},
    "vara_origem":{"type":"string"},
    "confianca":{"type":"string","enum":["ALTA","MEDIA","BAIXA"]}
  },
  "required":["e_merito_aereo","micro_tese","resultado_consumidor","dano_moral_concedido",
              "dano_moral_valor_reais","dano_material_concedido","fundamentos","prova_decisiva","confianca"]
}
SYSTEM=("Você é analista de jurimetria de acórdãos das Turmas Recursais (JEC/BA) em transporte aéreo. "
        "Baseie-se SOMENTE no texto. 'resultado_consumidor' é a procedência final para o AUTOR/consumidor: "
        "GANHOU (pedidos acolhidos), PARCIAL (parte acolhida), PERDEU (improcedência mantida). "
        "Não invente valores nem fundamentos; campo ausente = vazio/0.")

def extrair(client, model, conteudo):
    r=client.messages.create(model=model, max_tokens=1500, system=SYSTEM,
        output_config={"format":{"type":"json_schema","schema":SCHEMA}},
        messages=[{"role":"user","content":f"Extraia os dados deste acórdão:\n\n{conteudo[:18000]}"}])
    return json.loads(next(b.text for b in r.content if b.type=="text"))

def wilson(k,n,z=1.96):
    if n==0: return (0.0,0.0,0.0)
    p=k/n; d=1+z*z/n
    c=(p+z*z/(2*n))/d
    m=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (round(100*p), round(100*(c-m)), round(100*(c+m)))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("infile")
    ap.add_argument("--limit",type=int,default=0); ap.add_argument("--out",default="aereo_estruturado.jsonl")
    args=ap.parse_args()
    client=anthropic.Anthropic()
    rows=[json.loads(l) for l in open(args.infile,encoding="utf-8")]
    if args.limit: rows=rows[:args.limit]

    dados=[]; concord=0; validos=0
    with open(args.out,"w",encoding="utf-8") as fh:
        for i,r in enumerate(rows,1):
            c=r.get("conteudo","")
            try:
                a=extrair(client,MODEL_A,c); b=extrair(client,MODEL_B,c)
            except Exception as e:
                print(f"[{i}] ERRO {r.get('numeroProcesso')}: {e}",file=sys.stderr); continue
            # descarta se qualquer modelo diz que não é mérito aéreo
            if not (a["e_merito_aereo"] and b["e_merito_aereo"]): continue
            validos+=1
            acordo = (a["micro_tese"]==b["micro_tese"] and a["resultado_consumidor"]==b["resultado_consumidor"])
            if acordo: concord+=1
            reg={**a,"_concordancia":acordo,"numeroProcesso":r.get("numeroProcesso"),
                 "orgaoJulgador":r.get("orgaoJulgador"),"relator":r.get("relator"),
                 "dataJulgamento":r.get("dataJulgamento"),
                 "_divergencia":None if acordo else {"A":{"t":a["micro_tese"],"r":a["resultado_consumidor"]},
                                                     "B":{"t":b["micro_tese"],"r":b["resultado_consumidor"]}}}
            dados.append(reg); fh.write(json.dumps(reg,ensure_ascii=False)+"\n")
            print(f"[{i}/{len(rows)}] {r.get('numeroProcesso')} {a['micro_tese']}/{a['resultado_consumidor']} {'=' if acordo else 'DIVERGE'}",file=sys.stderr)
            time.sleep(0.2)

    # ---- 3) métrica de confiabilidade ----
    taxa=round(100*concord/validos) if validos else 0
    alta=[d for d in dados if d["_concordancia"]]   # só os concordantes entram no %

    # ---- 4) agregação com IC (sobre o conjunto de alta confiança) ----
    def pct_por(chave, favset=("GANHOU","PARCIAL")):
        g=defaultdict(lambda:[0,0])
        for d in alta:
            k=d.get(chave) or "(n/d)"; g[k][1]+=1
            if d["resultado_consumidor"] in favset: g[k][0]+=1
        out=[]
        for k,(kk,n) in sorted(g.items(),key=lambda x:-x[1][1]):
            p,lo,hi=wilson(kk,n); out.append((k,n,p,lo,hi))
        return out

    print("\n================ RESULTADO VALIDADO (tese AÉREO) ================",file=sys.stderr)
    print(f"Decisões válidas: {validos} | concordância entre {MODEL_A} e {MODEL_B}: {taxa}% "
          f"({concord}/{validos})  -> {len(alta)} casos de ALTA confiança usados no cálculo.",file=sys.stderr)
    print("\n% ÊXITO (ganhou+parcial) POR MICRO-TESE  [n · % · IC95%]:",file=sys.stderr)
    for k,n,p,lo,hi in pct_por("micro_tese"):
        print(f"   {k:20} n={n:3}  {p:3}%   IC[{lo}–{hi}]",file=sys.stderr)
    print("\n% ÊXITO POR RELATOR (n>=5):",file=sys.stderr)
    for k,n,p,lo,hi in pct_por("relator"):
        if n>=5: print(f"   {str(k)[:34]:34} n={n:3}  {p:3}%  IC[{lo}–{hi}]",file=sys.stderr)
    # dano moral
    dm=[d for d in alta if d["dano_moral_concedido"]]
    valores=[d["dano_moral_valor_reais"] for d in dm if d.get("dano_moral_valor_reais")]
    if alta:
        p,lo,hi=wilson(len(dm),len(alta))
        print(f"\nDANO MORAL concedido: {p}% (IC[{lo}–{hi}]) | mediana R$ {int(statistics.median(valores)) if valores else 0} | "
              f"faixa R$ {int(min(valores)) if valores else 0}–{int(max(valores)) if valores else 0}",file=sys.stderr)
    # divergências p/ revisão humana (o que vira padrão-ouro depois)
    div=[d for d in dados if not d["_concordancia"]]
    open("aereo_divergencias.jsonl","w",encoding="utf-8").write("\n".join(json.dumps(d,ensure_ascii=False) for d in div))
    print(f"\n{len(div)} divergências salvas em aereo_divergencias.jsonl (fila de revisão humana / futuro padrão-ouro).",file=sys.stderr)
    print(f"Estruturado -> {args.out}",file=sys.stderr)

if __name__=="__main__": main()
