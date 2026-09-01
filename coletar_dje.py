#!/usr/bin/env python3
"""
FASE 2 — Coletor de SENTENÇAS de 1º GRAU dos JUIZADOS ESPECIAIS (BA) via DJEN.
Fonte: API pública do Comunica/PJe (CNJ) — Diário de Justiça Eletrônico Nacional.
  https://comunicaapi.pje.jus.br/api/v1/comunicacao   (consulta é gratuita, sem login)

Fecha a lacuna do concorrente (AeroJuris): dado por COMARCA / VARA / JUIZ de 1º grau.
Filtra: siglaTribunal=TJBA · tipoDocumento=Sentença · órgão = JUIZADO ESPECIAL.
Grátis (só HTTP). Dedup por processo. Saída: corpus_dje.jsonl

Uso:  python3 coletar_dje.py [ALVO]     # ALVO padrão 8000 (piloto); use 0 p/ sem teto
"""
import json, urllib.request, urllib.parse, time, sys, os, re, datetime as dt

EP="https://comunicaapi.pje.jus.br/api/v1/comunicacao"
TRIB="TJBA"
DI=(dt.date.today()-dt.timedelta(days=3*365)).isoformat()   # últimos 3 anos
DF=dt.date.today().isoformat()
ALVO=int(sys.argv[1]) if len(sys.argv)>1 else 8000
OUT="corpus_dje.jsonl"
ITENS=100          # por página
MAX_PAG=60         # teto por tese

# (setor, frase de busca) — mesmas teses do acervo, agora no 1º grau
TESES=[
 ("FINANCEIRO","negativação indevida"),("FINANCEIRO","empréstimo consignado"),
 ("FINANCEIRO","desconto indevido"),("FINANCEIRO","cobrança indevida"),
 ("FRAUDE","transação não reconhecida"),("FRAUDE","golpe do pix"),("FRAUDE","engenharia social"),
 ("AEREO","extravio de bagagem"),("AEREO","atraso de voo"),("AEREO","cancelamento de voo"),
 ("SAUDE","negativa de cobertura"),("SAUDE","plano de saúde"),("SAUDE","reajuste abusivo"),
 ("COELBA","recuperação de consumo"),("COELBA","Coelba"),
 ("EMBASA","Embasa"),("TELECOM","serviço não solicitado"),
 ("ECOMMERCE","produto com defeito"),("ECOMMERCE","compra online"),
 ("CONSUMO","publicidade enganosa"),("APOSTAS","casa de apostas"),
]
DOISGRAU=("TURMA RECURSAL","CÂMARA","CAMARA","DESEMBARGADOR","DES.","RELATOR","2º JULGADOR","2O JULGADOR")
def eh_1grau(orgao):
    o=(orgao or "").upper()
    if not o: return False
    return not any(m in o for m in DOISGRAU)
def foro_tipo(orgao):
    o=(orgao or "").upper()
    if "JUIZADO" in o or "SISTEMA DOS JUIZADOS" in o: return "JUIZADO_ESPECIAL"
    if "RELA" in o and "CONS" in o: return "VARA_CONSUMO"
    if "CÍVEL" in o or "CIVEL" in o or "CÍVEIS" in o or "CIVEIS" in o: return "VARA_CIVEL"
    return "OUTRO_1G"
def comarca_de(orgao):
    o=(orgao or "").upper()
    m=re.search(r"COMARCA DE ([A-ZÁÂÃÉÊÍÓÔÕÚÇ'\. ]+)", o)
    if m: return re.sub(r"\s+"," ",m.group(1)).strip().title()
    m=re.search(r" DE ([A-ZÁÂÃÉÊÍÓÔÕÚÇ'\. ]{3,})$", o)
    return re.sub(r"\s+"," ",m.group(1)).strip().title() if m else None
RE_JUIZ=re.compile(r"([A-ZÁÂÃÉÊÍÓÔÕÚÇ][A-ZÁÂÃÉÊÍÓÔÕÚÇ\.\s]{6,55}?)\s+JU[ÍI]Z[A]?\s+DE\s+DIREITO")
def juiz_de(texto):
    m=RE_JUIZ.search((texto or "")[-1200:]) or RE_JUIZ.search(texto or "")
    if not m: return None
    nome=re.sub(r"\s+"," ",m.group(1)).strip().title()
    return nome if 8<=len(nome)<=55 else None

def pega(frase,pagina):
    qs=urllib.parse.urlencode({"siglaTribunal":TRIB,"texto":frase,"pagina":pagina,"itensPorPagina":ITENS,
        "dataDisponibilizacaoInicio":DI,"dataDisponibilizacaoFim":DF})
    r=urllib.request.Request(EP+"?"+qs,headers={"accept":"application/json","user-agent":"sondajus/1.0"})
    for _ in range(4):
        try:
            with urllib.request.urlopen(r,timeout=60) as x: d=json.loads(x.read())
            return d.get("items") or []
        except Exception: time.sleep(2)
    return []

def main():
    vis={}
    if os.path.exists(OUT):
        for l in open(OUT,encoding="utf-8"):
            try: vis[json.loads(l)["numeroProcesso"]]=1
            except Exception: pass
        print(f"resume: {len(vis)} já coletados",file=sys.stderr)
    fh=open(OUT,"a",encoding="utf-8")
    for setor,frase in TESES:
        if ALVO and len(vis)>=ALVO: break
        novos=0; p=1; vazias=0
        while p<=MAX_PAG and (not ALVO or len(vis)<ALVO):
            its=pega(frase,p)
            if not its:
                vazias+=1
                if vazias>=2: break
                p+=1; continue
            vazias=0
            for i in its:
                if i.get("tipoDocumento")!="Sentença": continue
                org=i.get("nomeOrgao")
                if not eh_1grau(org): continue
                pn=i.get("numeroprocessocommascara") or i.get("numero_processo")
                if not pn or pn in vis: continue
                txt=i.get("texto") or ""
                vis[pn]=1; novos+=1
                fh.write(json.dumps({
                    "numeroProcesso":pn,"tribunal":"TJBA","fonte":"DJEN","instancia":"1G",
                    "foro_tipo":foro_tipo(org),"setor":setor,"tese_busca":frase,
                    "orgaoJulgador":org,"comarca":comarca_de(org),"juiz":juiz_de(txt),
                    "classe":i.get("nomeClasse"),"dataJulgamento":(i.get("data_disponibilizacao") or "")[:10],
                    "link":i.get("link"),"conteudo":txt},ensure_ascii=False)+"\n")
            fh.flush(); p+=1; time.sleep(0.15)
        print(f"  {setor:11} {frase:28} +{novos} (acum {len(vis)})",file=sys.stderr)
    fh.close()
    print(f"\nTOTAL sentenças 1º grau (Juizados BA): {len(vis)} -> {OUT}",file=sys.stderr)

if __name__=="__main__": main()
