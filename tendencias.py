#!/usr/bin/env python3
"""
Módulo TESES EMERGENTES (Juizados Especiais BA — Turmas Recursais).
Detecta teses que estão SURGINDO comparando duas janelas de 12 meses:
  - ANTIGA   : ~3 anos atrás (42–30 meses)   -> a tese existia antes?
  - RECENTE  : ~último ano (15–3 meses)       -> aparece agora? (evita o edge de indexação)
Emergência = recente / antigo. Tese que era ~0 antes e tem volume agora = NOVA/SURGINDO.
Exporta emergentes.json.
"""
import json, urllib.request, time, datetime as dt, sys
from guias import guia

EP="https://jurisprudenciaws.tjba.jus.br/graphql"
Q="query f($f:DecisaoFilter!,$p:Int!,$i:Int!){ filter(decisaoFilter:$f,pageNumber:$p,itemsPerPage:$i){ itemCount } }"
QP="query f($f:DecisaoFilter!,$p:Int!,$i:Int!){ filter(decisaoFilter:$f,pageNumber:$p,itemsPerPage:$i){ decisoes{ numeroProcesso dataJulgamento } } }"
hoje=dt.date.today()
def d(m): return (hoje-dt.timedelta(days=int(m*30.44))).isoformat()
ANT_I,ANT_F = d(42),d(30)     # janela antiga (12m, ~3 anos atrás)
REC_I,REC_F = d(15),d(3)      # janela recente (12m, longe do atraso de indexação)
REC6_I,REC6_F = d(9),d(3)     # últimos 6 meses (9–3 mo, evita atraso de indexação)
PRE6_I,PRE6_F = d(15),d(9)    # 6 meses anteriores (15–9 mo)

def mk(a,di,df):
    return {"assunto":a,"numeroRecurso":"","orgaos":[],"relatores":[],"classes":[],"dataInicial":di,"dataFinal":df,
            "segundoGrau":False,"turmasRecursais":True,"tipoAcordaos":True,"tipoDecisoesMonocraticas":True,"ordenadoPor":"dataPublicacao"}
def c(a,di,df):
    body=json.dumps({"query":Q,"variables":{"f":mk(a,di,df),"p":1,"i":1}}).encode()
    r=urllib.request.Request(EP,data=body,method="POST",headers={"content-type":"application/json","origin":"https://jurisprudencia.tjba.jus.br","referer":"https://jurisprudencia.tjba.jus.br/"})
    for _ in range(3):
        try:
            j=json.loads(urllib.request.urlopen(r,timeout=60).read())
            if j.get("errors"): raise RuntimeError(j["errors"][0]["message"])
            return j["data"]["filter"]["itemCount"]
        except Exception as e: last=e; time.sleep(2)
    return -1

def procs(a,di,df,n=25):
    """amostra de números de processo reais da janela recente (auditoria)."""
    body=json.dumps({"query":QP,"variables":{"f":mk(a,di,df),"p":1,"i":n}}).encode()
    r=urllib.request.Request(EP,data=body,method="POST",headers={"content-type":"application/json","origin":"https://jurisprudencia.tjba.jus.br","referer":"https://jurisprudencia.tjba.jus.br/"})
    for _ in range(3):
        try:
            j=json.loads(urllib.request.urlopen(r,timeout=60).read())
            if j.get("errors"): raise RuntimeError(j["errors"][0]["message"])
            ds=j["data"]["filter"]["decisoes"] or []
            return [{"n":d.get("numeroProcesso"),"d":(d.get("dataJulgamento") or "")[:10]} for d in ds if d.get("numeroProcesso")]
        except Exception: time.sleep(2)
    return []

# candidatos = fenômenos recentes / marcos legais novos (+ alguns clássicos p/ contraste)
CAND=[
 ("Golpe do PIX",'"golpe do pix"',"FRAUDE"),
 ("Engenharia social / falsa central",'"engenharia social"',"FRAUDE"),
 ("Golpe do motoboy / cartão",'"golpe do motoboy"',"FRAUDE"),
 ("PIX (devolução/erro)",'"devolução do pix"',"FRAUDE"),
 ("Biometria facial (fraude)",'"biometria facial"',"FRAUDE"),
 ("Conta digital",'"conta digital"',"FRAUDE"),
 ("Descontos de associação/entidade",'"desconto associativo"',"FINANCEIRO"),
 ("Desconto não autorizado (benefício)",'"desconto não autorizado"',"FINANCEIRO"),
 ("Superendividamento (Lei 14.181)",'"superendividamento"',"FINANCEIRO"),
 ("Rol exemplificativo (Lei 14.454)",'"rol exemplificativo"',"SAUDE"),
 ("Rol da ANS",'"rol da ANS"',"SAUDE"),
 ("Reajuste abusivo (plano de saúde)",'"reajuste abusivo"',"SAUDE"),
 ("Negativa de cirurgia reparadora",'"cirurgia reparadora"',"SAUDE"),
 ("Telemedicina",'"telemedicina"',"SAUDE"),
 ("Site/loja falsa",'"loja falsa"',"CONSUMO_DIGITAL"),
 ("Marketplace (responsabilidade)",'"marketplace"',"CONSUMO_DIGITAL"),
 ("Motorista de aplicativo",'"motorista de aplicativo"',"CONSUMO_DIGITAL"),
 ("Streaming (cobrança)",'"assinatura de streaming"',"CONSUMO_DIGITAL"),
 ("Criptomoeda / pirâmide",'"pirâmide financeira"',"CONSUMO_DIGITAL"),
 ("Inteligência artificial / deepfake",'"inteligência artificial"',"CONSUMO_DIGITAL"),

 ("Casa de apostas / bet",'"casa de apostas"',"APOSTAS"),
 ("Aposta online / bet (bloqueio)",'"apostas esportivas"',"APOSTAS"),
 ("WhatsApp clonado",'"whatsapp clonado"',"FRAUDE"),
 ("Bloqueio de conta WhatsApp/Meta",'"whatsapp business"',"CONSUMO_DIGITAL"),
 ("Falso funcionário do banco",'"falso funcionário"',"FRAUDE"),
 ("Delivery / aplicativo de comida",'"aplicativo de entrega"',"CONSUMO_DIGITAL"),
 ("Energia solar (fotovoltaica)",'"energia solar"',"CONSUMO_DIGITAL"),
 ("Assinatura recorrente / clube",'"assinatura recorrente"',"CONSUMO_DIGITAL"),
 ("Consórcio (desistência)",'"desistência de consórcio"',"FINANCEIRO"),
 # clássicos p/ contraste (não devem ser 'novos')
 ("Negativação indevida (clássica)",'"negativação indevida"',"FINANCEIRO"),
 ("Empréstimo consignado (clássico)",'"empréstimo consignado"',"FINANCEIRO"),
]

def classificar(ant,rec):
    if rec<0 or ant<0: return "SEM_DADO",None
    ratio = round(rec/max(ant,1),2)
    if ant<=3 and rec>=8:   return "NOVA",ratio          # praticamente inexistia
    if rec>=15 and ratio>=2.0: return "SURGINDO",ratio    # multiplicou
    if ratio>=1.3 and rec>=10: return "CRESCENDO",ratio
    if ratio<=0.7 and ant>=10: return "DECLINANDO",ratio
    return "ESTAVEL",ratio

def main():
    print(f"antiga [{ANT_I}..{ANT_F}]  recente [{REC_I}..{REC_F}]\n", file=sys.stderr)
    out=[]
    print(f"{'TESE':38} {'antigo':>6} {'recente':>7} {'x':>5}  status", file=sys.stderr)
    for label,frase,setor in CAND:
        ant=c(frase,ANT_I,ANT_F); time.sleep(0.1)
        rec=c(frase,REC_I,REC_F); time.sleep(0.1)
        rec6=c(frase,REC6_I,REC6_F); time.sleep(0.1)
        pre6=c(frase,PRE6_I,PRE6_F); time.sleep(0.1)
        st,ratio=classificar(ant,rec)
        mult6=round(rec6/max(pre6,1),2) if (rec6>=0 and pre6>=0) else None
        item={"tese":label,"setor":setor,"frase":frase,"n_antigo":ant,"n_recente":rec,
              "n_recente_6m":rec6,"n_anterior_6m":pre6,"mult_6m":mult6,
              "multiplicador":ratio,"status":st,"guia":guia(label)}
        # anexa amostra de processos reais (auditoria) p/ teses emergentes OU com guia
        if st in ("NOVA","SURGINDO","CRESCENDO") or guia(label):
            item["processos"]=procs(frase,REC_I,REC_F,25); time.sleep(0.12)
        else:
            item["processos"]=[]
        out.append(item)
        print(f"{label:38} {ant:>6} {rec:>7} {str(ratio):>5}  {st}  guia:{'sim' if item['guia'] else '—'} procs:{len(item['processos'])}", file=sys.stderr)
    ordem={"NOVA":0,"SURGINDO":1,"CRESCENDO":2,"ESTAVEL":3,"DECLINANDO":4,"SEM_DADO":5}
    out.sort(key=lambda x:(ordem[x["status"]], -(x["multiplicador"] or 0)))
    json.dump({"gerado_em":hoje.isoformat(),"janela_antiga":[ANT_I,ANT_F],"janela_recente":[REC_I,REC_F],"teses":out},
              open("emergentes.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
    novas=[x for x in out if x["status"] in ("NOVA","SURGINDO")]
    print(f"\n{len(novas)} teses NOVAS/SURGINDO. -> emergentes.json", file=sys.stderr)

if __name__=="__main__": main()
