#!/usr/bin/env python3
"""
Análise AUTOMÁTICA (por marcadores, sem IA) sobre a base ampla (corpus_massa.jsonl).
Escala pra 10k+ instantaneamente. Extrai: sinal de resultado, réu, dano moral, turma.
NÃO é extração validada — é sinal agregado (rótulo honesto no produto).
Saída: base_massa.json
"""
import json, re, unicodedata, statistics, sys, datetime as dt
from collections import defaultdict, Counter

def norm(s): return re.sub(r"\s+"," ",unicodedata.normalize("NFKD",s or "").encode("ascii","ignore").decode().lower())

FAV=["dano moral configurad","dano moral caracteriz","dano moral devid","responsabilidade objetiva",
     "restituicao em dobro","repeticao em dobro","restituir em dobro","inexigibilidade do debito",
     "declarar a inexistencia","inexistencia do debito","condenar a re","condeno a re","condenar a acionada",
     "recurso conhecido e provido","sentenca reformada","procedente o pedido","procedentes os pedidos"]
UNFAV=["mero dissabor","mero aborrecimento","improceden","ausencia de prova","nao configurad",
       "ausencia de dano","exercicio regular","dano moral nao","meros aborrecimentos","recurso improvido",
       "negar provimento","nega-se provimento"]
def sinal(t):
    n=norm(t); f=sum(n.count(m) for m in FAV); u=sum(n.count(m) for m in UNFAV)
    return "FAV" if f>u else ("UNFAV" if u>f else "NEU")

# dicionário de réus (padrão no texto -> nome normalizado)
REUS=[
 (r"\bLATAM\b|TAM LINHAS|TAM S", "LATAM"),(r"\bGOL\b|GOL LINHAS","GOL"),(r"\bAZUL\b|AZUL LINHAS","AZUL"),
 (r"TRANSPORTES AEREOS PORTUGUESES|\bTAP\b","TAP"),(r"\bIBERIA\b","IBERIA"),(r"\bAVIANCA\b","AVIANCA"),(r"\bAMERICAN\b","AMERICAN"),
 (r"BRADESCO SAUDE","BRADESCO SAUDE"),(r"\bBRADESCO\b","BRADESCO"),(r"\bITAU\b|ITAUCARD|ITAU UNIBANCO","ITAU"),
 (r"\bSANTANDER\b","SANTANDER"),(r"CAIXA ECONOMICA|\bCEF\b","CAIXA"),(r"BANCO DO BRASIL|\bBB\b","BANCO DO BRASIL"),
 (r"\bNUBANK\b|NU PAGAMENTOS","NUBANK"),(r"BANCO PAN|\bPAN\b","BANCO PAN"),(r"\bBMG\b","BMG"),(r"\bC6\b","C6"),
 (r"MERCADO PAGO","MERCADO PAGO"),(r"MERCADO LIVRE|MERCADOLIVRE|EBAZAR","MERCADO LIVRE"),(r"PAGSEGURO|PAGBANK","PAGBANK"),
 (r"\bSAFRA\b","SAFRA"),(r"AGIBANK","AGIBANK"),(r"CREFISA","CREFISA"),(r"\bFACTA\b","FACTA"),(r"DAYCOVAL","DAYCOVAL"),
 (r"BANCO ORIGINAL","BANCO ORIGINAL"),(r"\bDIGIO\b","DIGIO"),(r"\bMERCANTIL\b","MERCANTIL"),(r"PARANA BANCO","PARANA BANCO"),
 (r"PICPAY","PICPAY"),(r"\bINTER\b","BANCO INTER"),(r"\bCREDZ\b","CREDZ"),
 (r"COMPANHIA DE ELETRICIDADE|\bCOELBA\b|NEOENERGIA","COELBA"),
 (r"EMPRESA BAIANA DE AGUAS|\bEMBASA\b","EMBASA"),
 (r"\bVIVO\b|TELEFONICA","VIVO"),(r"\bCLARO\b|\bNET\b|EMBRATEL","CLARO"),(r"\bTIM\b","TIM"),(r"\bOI\b|OI MOVEL|OI S","OI"),(r"\bSKY\b","SKY"),
 (r"\bUNIMED\b","UNIMED"),(r"\bHAPVIDA\b","HAPVIDA"),(r"\bAMIL\b","AMIL"),(r"SUL AMERICA|SULAMERICA","SULAMERICA"),
 (r"NOTREDAME|INTERMEDICA","NOTREDAME INTERMEDICA"),(r"\bPLANSERV\b","PLANSERV"),(r"\bGEAP\b","GEAP"),
 (r"MAGAZINE LUIZA|MAGALU|LUIZALABS","MAGAZINE LUIZA"),(r"CASAS BAHIA|VIA VAREJO|\bVIA S","CASAS BAHIA"),
 (r"\bAMAZON\b","AMAZON"),(r"\bSHOPEE\b","SHOPEE"),(r"AMERICANAS|B2W|SUBMARINO","AMERICANAS"),(r"\bNETSHOES\b","NETSHOES"),
 (r"\bNIKE\b","NIKE"),(r"\bADIDAS\b","ADIDAS"),(r"SAMSUNG","SAMSUNG"),(r"\bAPPLE\b","APPLE"),(r"\bSHEIN\b","SHEIN"),
 (r"CORA COLA|COCA-COLA|COCA COLA","COCA COLA"),(r"\bIFOOD\b","IFOOD"),(r"\bUBER\b","UBER"),(r"\b99\b|99 TECNOLOGIA","99"),
]
REUS_C=[(re.compile(p),n) for p,n in REUS]
def acha_reu(cab):
    for rx,nome in REUS_C:
        if rx.search(cab): return nome
    return None

RE_VAL=re.compile(r"dano[s]? mora[li][s]?[^R$]{0,120}?R\$\s?([\d\.]+,\d{2}|[\d\.]{3,})", re.I)
def valor_dm(t):
    m=RE_VAL.search(t)
    if not m: return None
    s=re.sub(r"[^0-9,\.]","",m.group(1))
    if "," in s and "." in s: s=s.replace(".","").replace(",",".")
    elif "," in s: s=s.replace(",",".")
    try:
        v=float(s); return v if 200<=v<=100000 else None
    except: return None

def carregar(files):
    vis=set(); rows=[]
    for fn in files:
        try: fh=open(fn,encoding="utf-8")
        except FileNotFoundError: continue
        for l in fh:
            try: r=json.loads(l)
            except Exception: continue
            pn=r.get("numeroProcesso")
            if pn and pn in vis: continue
            if pn: vis.add(pn)
            rows.append(r)
    return rows

def main():
    # aceita arquivos por argumento; padrão = base ampliada (50k) + base original, dedup
    files=sys.argv[1:] or ["corpus_50k.jsonl","corpus_massa.jsonl"]
    rows=carregar(files)
    setor_ag=defaultdict(lambda:{"n":0,"fav":0,"unf":0,"dm":0,"vals":[]})
    reu_ag=defaultdict(lambda:{"n":0,"fav":0,"unf":0})
    registros=[]
    for r in rows:
        cont=r.get("conteudo") or ""
        sg=sinal(cont)
        cabU=(cont[:900]).upper()
        cabU=unicodedata.normalize("NFKD",cabU).encode("ascii","ignore").decode()
        reu=acha_reu(cabU)
        v=valor_dm(cont)
        registros.append({"s":r["setor"],"t":r.get("tese_busca"),"a":(r.get("dataJulgamento") or "")[:4] or None,
                          "r":reu,"g":sg[0]})
        a=setor_ag[r["setor"]]
        a["n"]+=1
        if sg=="FAV": a["fav"]+=1
        elif sg=="UNFAV": a["unf"]+=1
        if v: a["dm"]+=1; a["vals"].append(v)
        if reu:
            b=reu_ag[reu]; b["n"]+=1
            if sg=="FAV": b["fav"]+=1
            elif sg=="UNFAV": b["unf"]+=1
    setores=[]
    for s,a in sorted(setor_ag.items(),key=lambda x:-x[1]["n"]):
        dec=a["fav"]+a["unf"]
        setores.append({"setor":s,"n":a["n"],
            "pct_fav_sinal":round(100*a["fav"]/dec) if dec else None,
            "dano_moral_mediana":int(statistics.median(a["vals"])) if a["vals"] else 0})
    reus=[]
    for r,b in sorted(reu_ag.items(),key=lambda x:-x[1]["n"]):
        dec=b["fav"]+b["unf"]
        if b["n"]>=8:
            reus.append({"reu":r,"n":b["n"],"pct_fav_sinal":round(100*b["fav"]/dec) if dec else None})
    reus.sort(key=lambda x:-x["n"])
    out={"total":len(rows),"gerado_em":dt.date.today().isoformat(),"setores":setores,"reus":reus[:20]}
    json.dump(out,open("base_massa.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
    json.dump(registros,open("registros_massa.json","w",encoding="utf-8"),ensure_ascii=False)  # p/ filtro por ano/tese
    print(f"análise automática: {len(rows)} processos · {len(setores)} setores · {len(reus)} réus")
    for s in setores: print(f"  {s['setor']:11} n={s['n']:5}  sinal FAV {s['pct_fav_sinal']}%")

if __name__=="__main__": main()
