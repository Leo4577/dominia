#!/usr/bin/env python3
"""
JUIZADOS via DATAJUD (CNJ) — cobre o que o DJEN não cobre (Projudi).
Traz METADADOS: tese (assunto), órgão/comarca e RESULTADO (movimentos CNJ). NÃO traz íntegra.
API pública, sem captcha. Chave vigente na Wiki: https://datajud-wiki.cnj.jus.br/api-publica/acesso/

Saída: datajud_juizado.json (procedência por tese e por comarca, só Juizado).
Uso:  python3 coletar_datajud.py [MAX_PAGINAS]   # cada página = 1000 processos
"""
import urllib.request, json, sys, time, re
from collections import defaultdict

EP="https://api-publica.datajud.cnj.jus.br/api_publica_tjba/_search"
KEY="APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="  # trocar se o CNJ girar a chave
MAXPAG=int(sys.argv[1]) if len(sys.argv)>1 else 30
# códigos de movimento CNJ (VERIFICADOS na base do TJBA)
WIN={219,221}     # Procedência / Procedência em Parte
LOSS={220}        # Improcedência
ACORDO={466,471}  # Homologação de Transação / de acordo
# 463=Desistência, 196=Extinção execução -> não são mérito, ficam de fora do % de êxito

def resultado_mov(movs):
    cods={m.get("codigo") for m in movs}
    if cods & WIN: return "PROCEDENTE"
    if cods & ACORDO: return "ACORDO"
    if cods & LOSS: return "IMPROCEDENTE"
    return None   # sem resultado de mérito (pendente/desistência/extinção) -> não conta no %

def norm(s): return re.sub(r"\s+"," ",(s or "")).strip()
def comarca_de(orgao):
    o=(orgao or "").upper()
    m=re.search(r"COMARCA DE ([A-ZÁÂÃÉÊÍÓÔÕÚÇ ]+)",o) or re.search(r"\bDE ([A-ZÁÂÃÉÊÍÓÔÕÚÇ ]{3,})$",o)
    if m: return norm(m.group(1)).title()
    if "SALVADOR" in o or "CAPITAL" in o: return "Salvador"
    return None
# assunto -> setor (agrupa a taxonomia do CNJ nos nossos setores)
def setor_de(assuntos):
    a=" ".join(assuntos).lower()
    if any(k in a for k in["bagagem","voo","transporte aéreo","aéreo"]): return "AEREO"
    if any(k in a for k in["plano de saúde","seguro saúde","tratamento médico"]): return "SAUDE"
    if any(k in a for k in["energia elétrica","fornecimento de energia"]): return "COELBA"
    if any(k in a for k in["água","esgoto"]): return "EMBASA"
    if any(k in a for k in["telefonia","telecomunicaç","internet"]): return "TELECOM"
    if any(k in a for k in["fraude","estelionato","transação não reconhecida"]): return "FRAUDE"
    if any(k in a for k in["cadastro de inadimplentes","negativ","empréstimo","bancár","cartão","tarifa","consignado","dano material"]): return "FINANCEIRO"
    return "CONSUMO"

def busca(search_after=None):
    q={"size":1000,"query":{"match_phrase":{"classe.nome":"Procedimento do Juizado Especial Cível"}},
       "sort":[{"@timestamp":{"order":"asc"}}]}
    if search_after: q["search_after"]=search_after
    r=urllib.request.Request(EP,data=json.dumps(q).encode(),method="POST",
        headers={"Authorization":KEY,"Content-Type":"application/json"})
    for _ in range(4):
        try:
            with urllib.request.urlopen(r,timeout=60) as x: return json.loads(x.read())
        except Exception as e: last=e; time.sleep(3)
    print("falha:",last,file=sys.stderr); return None

def main():
    # só MÉRITO (procedência x improcedência); acordo (466) é ambíguo sem a íntegra e fica fora do %
    tese=defaultdict(lambda:{"win":0,"loss":0,"acordo":0})
    comarca=defaultdict(lambda:{"win":0,"loss":0})
    total=0; merito=0; sa=None
    for p in range(MAXPAG):
        d=busca(sa)
        if not d: break
        hits=d.get("hits",{}).get("hits",[])
        if not hits: break
        for h in hits:
            s=h["_source"]; total+=1
            res=resultado_mov(s.get("movimentos") or [])
            if not res: continue
            setor=setor_de([a.get("nome","") for a in (s.get("assuntos") or [])])
            c=comarca_de((s.get("orgaoJulgador") or {}).get("nome"))
            t=tese[setor]
            if res=="PROCEDENTE": t["win"]+=1; merito+=1
            elif res=="IMPROCEDENTE": t["loss"]+=1; merito+=1
            elif res=="ACORDO": t["acordo"]+=1
            if c and res in ("PROCEDENTE","IMPROCEDENTE"):
                cm=comarca[c];
                if res=="PROCEDENTE": cm["win"]+=1
                else: cm["loss"]+=1
        sa=hits[-1].get("sort")
        print(f"  página {p+1}: total {total}, mérito {merito}",file=sys.stderr)
        time.sleep(0.3)
    def pct(w,l): return round(100*w/(w+l)) if (w+l) else None
    teses=sorted([{"setor":k,"n":v["win"]+v["loss"],"pct_proc":pct(v["win"],v["loss"]),"n_acordo":v["acordo"]}
                  for k,v in tese.items() if v["win"]+v["loss"]>=15], key=lambda x:-x["n"])
    comarcas=sorted([{"comarca":k,"n":v["win"]+v["loss"],"pct":pct(v["win"],v["loss"])}
                     for k,v in comarca.items() if v["win"]+v["loss"]>=15],key=lambda x:-x["n"])
    out={"fonte":"Datajud/CNJ","foro":"JUIZADO","total_processos":total,"merito":merito,
         "obs":"procedência entre decisões de mérito (219/221 vs 220); acordo excluído (ambíguo); sem íntegra/dano moral",
         "por_setor":teses,"comarcas":comarcas}
    json.dump(out,open("datajud_juizado.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
    print(f"\nJUIZADO via Datajud: {total} processos, {merito} decisões de mérito")
    print("procedência por setor (Juizado, entre mérito):")
    for t in teses[:8]: print(f"  {t['setor']:11} n={t['n']:5}  procedência {t['pct_proc']}%")

if __name__=="__main__": main()
