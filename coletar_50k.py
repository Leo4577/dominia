#!/usr/bin/env python3
"""
Coleta AMPLIADA rumo a 50k (Juizados Especiais BA / Turmas Recursais), últimos 3 anos.
Guarda o INTEIRO TEOR COMPLETO (necessário para validação por IA depois).
Grátis (só HTTP). Dedup global por processo. Resumível: relê o que já existe e continua.
Saída: corpus_50k.jsonl  (append-safe)

Uso:  python3 coletar_50k.py [ALVO]     # ALVO padrão 50000
"""
import json, urllib.request, time, sys, os
EP="https://jurisprudenciaws.tjba.jus.br/graphql"
Q=("query f($f:DecisaoFilter!,$p:Int!,$i:Int!){ filter(decisaoFilter:$f,pageNumber:$p,itemsPerPage:$i){ "
   "decisoes{ numeroProcesso tipoDecisao dataJulgamento orgaoJulgador{ nome } relator{ nome } classe{ descricao } conteudo } } }")
DI="2023-08-19"          # últimos ~3 anos
ALVO=int(sys.argv[1]) if len(sys.argv)>1 else 50000
OUT="corpus_50k.jsonl"
MAX_PAGES=120            # teto por frase (~3.600 resultados) — evita loop infinito
CONT_MAX=15000          # inteiro teor p/ validação (não truncar o dispositivo)

# (setor, frase de busca EXATA com acentos) — ampla cobertura das teses do JEC BA
TESES=[
 # --- FINANCEIRO / BANCÁRIO ---
 ("FINANCEIRO",'"negativação indevida"'),("FINANCEIRO",'"inscrição indevida"'),
 ("FINANCEIRO",'"empréstimo consignado"'),("FINANCEIRO",'"empréstimo não contratado"'),
 ("FINANCEIRO",'"desconto indevido"'),("FINANCEIRO",'"desconto em benefício"'),
 ("FINANCEIRO",'"transação não reconhecida"'),("FINANCEIRO",'"saque indevido"'),
 ("FINANCEIRO",'"tarifa bancária"'),("FINANCEIRO",'"cartão de crédito"'),
 ("FINANCEIRO",'"cobrança indevida"'),("FINANCEIRO",'"superendividamento"'),
 ("FINANCEIRO",'"cartão consignado"'),("FINANCEIRO",'"revisão contratual"'),
 ("FINANCEIRO",'"juros abusivos"'),("FINANCEIRO",'"capitalização de juros"'),
 ("FINANCEIRO",'"seguro prestamista"'),("FINANCEIRO",'"portabilidade de salário"'),
 # --- FRAUDE / GOLPE ---
 ("FRAUDE",'"golpe do falso"'),("FRAUDE",'"estelionato"'),("FRAUDE",'"pix"'),
 ("FRAUDE",'"biometria facial"'),("FRAUDE",'"engenharia social"'),("FRAUDE",'"conta digital"'),
 ("FRAUDE",'"fraude bancária"'),("FRAUDE",'"clonagem"'),("FRAUDE",'"perfil falso"'),
 # --- AÉREO ---
 ("AEREO",'"extravio de bagagem"'),("AEREO",'"atraso de voo"'),("AEREO",'"cancelamento de voo"'),
 ("AEREO",'"overbooking"'),("AEREO",'"bagagem violada"'),("AEREO",'"conexão perdida"'),
 ("AEREO",'"reacomodação"'),("AEREO",'"voo cancelado"'),
 # --- SAÚDE ---
 ("SAUDE",'"negativa de cobertura"'),("SAUDE",'"plano de saúde"'),("SAUDE",'"reajuste por faixa etária"'),
 ("SAUDE",'"rol da ANS"'),("SAUDE",'"home care"'),("SAUDE",'"reembolso de despesas médicas"'),
 ("SAUDE",'"medicamento de alto custo"'),("SAUDE",'"carência"'),
 # --- ENERGIA (COELBA) ---
 ("COELBA",'"recuperação de consumo"'),("COELBA",'"Coelba"'),("COELBA",'"fatura de energia"'),
 ("COELBA",'"corte de energia"'),("COELBA",'"medidor"'),
 # --- ÁGUA (EMBASA) ---
 ("EMBASA",'"Embasa"'),("EMBASA",'"suspensão do fornecimento"'),("EMBASA",'"tarifa de esgoto"'),
 ("EMBASA",'"vazamento"'),
 # --- TELECOM ---
 ("TELECOM",'"telefonia"'),("TELECOM",'"serviço não solicitado"'),("TELECOM",'"internet"'),
 ("TELECOM",'"cobrança de serviço não contratado"'),("TELECOM",'"portabilidade"'),
 ("TELECOM",'"fatura de telefone"'),("TELECOM",'"cancelamento de plano"'),
 # --- E-COMMERCE / PRODUTO ---
 ("ECOMMERCE",'"vício do produto"'),("ECOMMERCE",'"atraso na entrega"'),("ECOMMERCE",'"produto com defeito"'),
 ("ECOMMERCE",'"produto não entregue"'),("ECOMMERCE",'"compra online"'),("ECOMMERCE",'"estorno"'),
 ("ECOMMERCE",'"troca de produto"'),
 # --- CONSUMO GERAL ---
 ("CONSUMO",'"publicidade enganosa"'),("CONSUMO",'"dano moral"'),("CONSUMO",'"vício de qualidade"'),
 ("CONSUMO",'"cláusula abusiva"'),("CONSUMO",'"inversão do ônus da prova"'),
 # --- APOSTAS / EMERGENTES ---
 ("APOSTAS",'"casa de apostas"'),("APOSTAS",'"bet"'),("APOSTAS",'"aposta esportiva"'),
]
def mk(a):
    return {"assunto":a,"numeroRecurso":"","orgaos":[],"relatores":[],"classes":[],"dataInicial":DI,"dataFinal":None,
            "segundoGrau":False,"turmasRecursais":True,"tipoAcordaos":True,"tipoDecisoesMonocraticas":True,"ordenadoPor":"dataPublicacao"}
def page(a,p,i=30):
    body=json.dumps({"query":Q,"variables":{"f":mk(a),"p":p,"i":i}}).encode()
    r=urllib.request.Request(EP,data=body,method="POST",headers={"content-type":"application/json","origin":"https://jurisprudencia.tjba.jus.br","referer":"https://jurisprudencia.tjba.jus.br/"})
    for _ in range(4):
        try:
            with urllib.request.urlopen(r,timeout=90) as x: d=json.loads(x.read())
            if d.get("errors"): raise RuntimeError(d["errors"][0]["message"])
            return d["data"]["filter"]["decisoes"] or []
        except Exception: time.sleep(2)
    return []

def main():
    vis={}
    # resume: carrega o que já foi coletado
    if os.path.exists(OUT):
        for l in open(OUT,encoding="utf-8"):
            try: vis[json.loads(l)["numeroProcesso"]]=1
            except Exception: pass
        print(f"resume: {len(vis)} já no arquivo",file=sys.stderr)
    fh=open(OUT,"a",encoding="utf-8")
    for setor,frase in TESES:
        if len(vis)>=ALVO: break
        novos=0; p=1; vazias=0
        while p<=MAX_PAGES and len(vis)<ALVO:
            decs=page(frase,p)
            if not decs:
                vazias+=1
                if vazias>=2: break
                p+=1; continue
            vazias=0
            for x in decs:
                pn=x.get("numeroProcesso")
                if not pn or pn in vis: continue
                vis[pn]=1; novos+=1
                rec={"numeroProcesso":pn,"tribunal":"TJBA","fonte":"TJBA-jurisprudencia","instancia":"JUIZADO",
                     "setor":setor,"tese_busca":frase.strip('"'),
                     "orgaoJulgador":(x.get("orgaoJulgador") or {}).get("nome"),
                     "relator":(x.get("relator") or {}).get("nome"),
                     "classe":(x.get("classe") or {}).get("descricao"),
                     "dataJulgamento":(x.get("dataJulgamento") or "")[:10],
                     "conteudo":(x.get("conteudo") or "")[:CONT_MAX]}
                fh.write(json.dumps(rec,ensure_ascii=False)+"\n")
            fh.flush(); p+=1; time.sleep(0.15)
        print(f"  {setor:11} {frase:38} +{novos} (acum {len(vis)})",file=sys.stderr)
    fh.close()
    print(f"\nTOTAL únicos: {len(vis)} -> {OUT}",file=sys.stderr)

if __name__=="__main__": main()
