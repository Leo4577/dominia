#!/usr/bin/env python3
"""
CENSO das sentenças de consumo de 1º grau da BA (DJEN/Comunica CNJ) — sem viés de tese.
Em vez de buscar por tese (amostra enviesada), busca por termos GUARDA-CHUVA que aparecem
em ~toda sentença consumerista ("relação de consumo", "consumidor") e filtra pelas Varas de
Consumo/Juizados. O SETOR é classificado pelo CONTEÚDO da sentença, não pela busca.
Janela por data (fura o teto de 10.000 por consulta). Grátis. Dedup. Inteiro teor.
Saída: corpus_censo.jsonl   (resumível)

Uso:  python3 coletar_censo.py [DIAS_JANELA]   # padrão 10
"""
import json, urllib.request, urllib.parse, time, sys, os, re, unicodedata, datetime as dt

EP="https://comunicaapi.pje.jus.br/api/v1/comunicacao"
UMBRELLA=["relação de consumo","consumidor"]     # aparecem em ~toda sentença de consumo
DIAS=int(sys.argv[1]) if len(sys.argv)>1 else 10
FIM=dt.date.today(); INI=FIM-dt.timedelta(days=3*365)
OUT="corpus_censo.jsonl"; ITENS=100; MAXPAG=100

def norm(s): return unicodedata.normalize("NFKD",(s or "").lower()).encode("ascii","ignore").decode()
def eh_consumo_1g(o):
    O=(o or "").upper()
    if any(m in O for m in ("TURMA RECURSAL","CÂMARA","CAMARA","DESEMBARGADOR","DES.","RELATOR")): return False
    return ("CONSUMO" in O) or ("JUIZADO ESPECIAL" in O) or ("SISTEMA DOS JUIZADOS" in O)
# classificador de setor pelo TEOR (não pela busca)
SETOR_KW=[
 ("AEREO",["voo","bagagem","aerea","companhia aerea","overbooking","latam","gol linhas","azul linhas","aeroporto","anac"]),
 ("SAUDE",["plano de saude","operadora","ans","cirurgia","medicamento","unimed","hapvida","amil","cobertura","carencia","home care"]),
 ("FRAUDE",["golpe","fraude","estelionato","transacao nao reconhecida","clonagem","engenharia social","pix"]),
 ("COELBA",["coelba","neoenergia","energia eletrica","fatura de energia","recuperacao de consumo","medidor"]),
 ("EMBASA",["embasa","agua e esgoto","fornecimento de agua","tarifa de esgoto"]),
 ("TELECOM",["telefonia","internet","banda larga","vivo","claro","tim ","oi movel","operadora de telefonia"]),
 ("ECOMMERCE",["compra online","entrega do produto","mercado livre","magazine luiza","americanas","shopee","produto com defeito","vicio do produto"]),
 ("APOSTAS",["aposta","casa de apostas"," bet ","bet365"]),
 ("FINANCEIRO",["banco","emprestimo","consignado","cartao de credito","negativacao","financiamento","tarifa bancaria","conta corrente","debito"]),
]
def setor_de(texto):
    n=norm(texto)[:6000]
    best,score="CONSUMO",0
    for s,kws in SETOR_KW:
        c=sum(n.count(k) for k in kws)
        if c>score: best,score=s,c
    return best

def pega(termo,di,df,p):
    qs=urllib.parse.urlencode({"siglaTribunal":"TJBA","texto":termo,"pagina":p,"itensPorPagina":ITENS,
        "dataDisponibilizacaoInicio":di,"dataDisponibilizacaoFim":df})
    r=urllib.request.Request(EP+"?"+qs,headers={"accept":"application/json","user-agent":"sondajus/1.0"})
    for _ in range(4):
        try:
            with urllib.request.urlopen(r,timeout=70) as x:
                return json.loads(x.read().decode("utf-8","replace"),strict=False).get("items") or []
        except Exception: time.sleep(2)
    return []

def main():
    vis={}
    if os.path.exists(OUT):
        for l in open(OUT,encoding="utf-8"):
            try: vis[json.loads(l)["numeroProcesso"]]=1
            except Exception: pass
        print(f"resume: {len(vis)} já coletadas",file=sys.stderr)
    fh=open(OUT,"a",encoding="utf-8")
    janela=INI; total0=len(vis)
    while janela<FIM:
        jf=min(janela+dt.timedelta(days=DIAS),FIM)
        di,df=janela.isoformat(),jf.isoformat()
        novos=0
        for termo in UMBRELLA:
            p=1; vazias=0
            while p<=MAXPAG:
                its=pega(termo,di,df,p)
                if not its:
                    vazias+=1
                    if vazias>=2: break
                    p+=1; continue
                vazias=0
                for i in its:
                    if i.get("tipoDocumento")!="Sentença": continue
                    if not eh_consumo_1g(i.get("nomeOrgao")): continue
                    pn=i.get("numeroprocessocommascara") or i.get("numero_processo")
                    if not pn or pn in vis: continue
                    txt=i.get("texto") or ""
                    vis[pn]=1; novos+=1
                    fh.write(json.dumps({"numeroProcesso":pn,"tribunal":"TJBA","fonte":"DJEN-censo",
                        "instancia":"1G","setor":setor_de(txt),"orgaoJulgador":i.get("nomeOrgao"),
                        "classe":i.get("nomeClasse"),"dataJulgamento":(i.get("data_disponibilizacao") or "")[:10],
                        "link":i.get("link"),"conteudo":txt},ensure_ascii=False)+"\n")
                if len(its)<ITENS: break
                p+=1; time.sleep(0.12)
        fh.flush()
        print(f"  {di}..{df}: +{novos} (acum {len(vis)})",file=sys.stderr)
        janela=jf
    fh.close()
    print(f"\nCENSO consumo 1º grau BA: {len(vis)} sentenças (+{len(vis)-total0}) -> {OUT}",file=sys.stderr)

if __name__=="__main__": main()
