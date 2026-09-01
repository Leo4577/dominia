#!/usr/bin/env python3
"""
Coleta em MASSA (Juizado / Turmas Recursais) — para a base ampla (10k+).
Guarda metadados + um trecho do inteiro teor (p/ análise automática por marcadores).
Grátis (só HTTP). Dedup por processo. Saída: corpus_massa.jsonl
"""
import json, urllib.request, time, sys
EP="https://jurisprudenciaws.tjba.jus.br/graphql"
Q=("query f($f:DecisaoFilter!,$p:Int!,$i:Int!){ filter(decisaoFilter:$f,pageNumber:$p,itemsPerPage:$i){ "
   "decisoes{ numeroProcesso tipoDecisao dataJulgamento orgaoJulgador{ nome } relator{ nome } classe{ descricao } conteudo } } }")
DI="2023-08-18"
POR_TESE=int(sys.argv[1]) if len(sys.argv)>1 else 550

# (setor, frase de busca)
TESES=[
 ("FINANCEIRO",'"negativação indevida"'),("FINANCEIRO",'"empréstimo consignado"'),
 ("FINANCEIRO",'"empréstimo não contratado"'),("FINANCEIRO",'"desconto indevido"'),
 ("FINANCEIRO",'"transação não reconhecida"'),("FINANCEIRO",'"golpe"'),("FINANCEIRO",'"tarifa bancária"'),
 ("FINANCEIRO",'"cartão de crédito"'),("FINANCEIRO",'"cobrança indevida"'),("FINANCEIRO",'"superendividamento"'),
 ("AEREO",'"extravio de bagagem"'),("AEREO",'"atraso de voo"'),("AEREO",'"cancelamento de voo"'),
 ("SAUDE",'"negativa de cobertura"'),("SAUDE",'"plano de saúde"'),("SAUDE",'"reajuste por faixa etária"'),
 ("SAUDE",'"rol da ANS"'),
 ("COELBA",'"recuperação de consumo"'),("COELBA",'"Coelba"'),
 ("EMBASA",'"Embasa"'),("EMBASA",'"suspensão do fornecimento"'),
 ("TELECOM",'"telefonia"'),("TELECOM",'"serviço não solicitado"'),("TELECOM",'"internet"'),
 ("ECOMMERCE",'"vício do produto"'),("ECOMMERCE",'"atraso na entrega"'),("ECOMMERCE",'"produto com defeito"'),
 ("CONSUMO",'"publicidade enganosa"'),("CONSUMO",'"cobrança de serviço não contratado"'),
 ("FRAUDE",'"biometria facial"'),("FRAUDE",'"engenharia social"'),("FRAUDE",'"conta digital"'),
 ("APOSTAS",'"casa de apostas"'),
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
        except Exception as e: time.sleep(2)
    return []

def main():
    vis={}
    fh=open("corpus_massa.jsonl","w",encoding="utf-8")
    for setor,frase in TESES:
        got=0; p=1
        while got<POR_TESE:
            decs=page(frase,p)
            if not decs: break
            for x in decs:
                pn=x.get("numeroProcesso")
                got+=1
                if not pn or pn in vis: continue
                vis[pn]=1
                rec={"numeroProcesso":pn,"tribunal":"TJBA","fonte":"TJBA-jurisprudencia","instancia":"JUIZADO",
                     "setor":setor,"tese_busca":frase.strip('"'),
                     "orgaoJulgador":(x.get("orgaoJulgador") or {}).get("nome"),
                     "relator":(x.get("relator") or {}).get("nome"),
                     "classe":(x.get("classe") or {}).get("descricao"),
                     "dataJulgamento":(x.get("dataJulgamento") or "")[:10],
                     "conteudo":(x.get("conteudo") or "")[:3800]}
                fh.write(json.dumps(rec,ensure_ascii=False)+"\n")
            p+=1; time.sleep(0.18)
        print(f"  {setor:11} {frase:34} +{got} (únicos acum: {len(vis)})", file=sys.stderr)
    fh.close()
    print(f"\nTOTAL únicos coletados: {len(vis)} -> corpus_massa.jsonl", file=sys.stderr)

if __name__=="__main__": main()
