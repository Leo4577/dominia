#!/usr/bin/env python3
"""
ATUALIZADOR DIÁRIO (self-contained, roda no GitHub Actions — sem o corpus gigante).
Busca as sentenças NOVAS de 1º grau (DJEN/Comunica, janela de dias) das mesmas teses,
extrai os campos com as funções do analise_dje e funde no registros_dje.json (dedup por processo).
Recalcula dje_stats.json a partir dos registros. Depois o workflow roda gerar_dashboard.py.
Uso: python3 atualizar_diario.py     (DIAS=7 e MAX_PAG=12 por env)
"""
import json, urllib.request, urllib.parse, time, os, re, datetime as dt, statistics
from collections import defaultdict, Counter
from analise_dje import resultado, valor_cond, acha_reu, comarca_de, juiz_de, foro, norm
from adicionar_ementa import ementa

EP="https://comunicaapi.pje.jus.br/api/v1/comunicacao"; TRIB="TJBA"; ITENS=100
DIAS=int(os.environ.get("DIAS","7"))
MAX_PAG=int(os.environ.get("MAX_PAG","12"))
DI=(dt.date.today()-dt.timedelta(days=DIAS)).isoformat()
DF=dt.date.today().isoformat()
OUT_REG="registros_dje.json"; OUT_STATS="dje_stats.json"

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
def eh_1grau(org):
    o=(org or "").upper()
    return bool(o) and not any(m in o for m in DOISGRAU)

def pega(frase,pagina):
    qs=urllib.parse.urlencode({"siglaTribunal":TRIB,"texto":frase,"pagina":pagina,"itensPorPagina":ITENS,
        "dataDisponibilizacaoInicio":DI,"dataDisponibilizacaoFim":DF})
    r=urllib.request.Request(EP+"?"+qs,headers={"accept":"application/json","user-agent":"dominia/1.0"})
    for _ in range(4):
        try:
            with urllib.request.urlopen(r,timeout=60) as x: return json.loads(x.read()).get("items") or []
        except Exception: time.sleep(2)
    return []

def rebuild_stats(reg):
    G=["JUIZADO","COMUM"]
    sr={g:defaultdict(lambda:[0,0]) for g in G}; sdm={g:defaultdict(list) for g in G}
    com={g:defaultdict(lambda:{"n":0,"proc":0,"dm":[]}) for g in G}
    reu={g:defaultdict(lambda:{"n":0,"proc":0,"dm":[]}) for g in G}
    cross={g:defaultdict(lambda:defaultdict(lambda:{"n":0,"proc":0,"dm":[]})) for g in G}
    juizes=Counter(); cidades=set(); foros=Counter()
    for r in reg:
        s=r.get("s"); g=r.get("fg") if r.get("fg") in G else "COMUM"
        res=r.get("res"); venceu=True if res in("PROCEDENTE","PARCIAL") else (False if res=="IMPROCEDENTE" else None)
        v=r.get("v"); c=r.get("c"); j=r.get("j"); rr=r.get("r")
        foros["JUIZADO_ESPECIAL" if g=="JUIZADO" else "OUTRO_1G"]+=1
        if j: juizes[j]+=1
        if c: cidades.add(c)
        if venceu is not None:
            sr[g][s][0]+=1
            if venceu: sr[g][s][1]+=1
        if v and venceu: sdm[g][s].append(v)
        if c:
            for D in (com[g][c], cross[g][s][c]):
                D["n"]+=1
                if venceu: D["proc"]+=1
                if v and venceu: D["dm"].append(v)
        if rr:
            reu[g][rr]["n"]+=1
            if venceu: reu[g][rr]["proc"]+=1
            if v and venceu: reu[g][rr]["dm"].append(v)
    med=lambda a:int(statistics.median(a)) if a else None
    def por_foro(g):
        dm_area=sorted([{"setor":s,"n_dm":len(sdm[g][s]),"mediana":med(sdm[g][s]),
                         "pct_dm":round(100*len(sdm[g][s])/sr[g][s][0]) if sr[g][s][0] else None}
                        for s in sr[g] if sr[g][s][0]>=20 and sdm[g][s]], key=lambda x:-(x["mediana"] or 0))
        exito=sorted([{"setor":s,"n":d[0],"pct":round(100*d[1]/d[0]) if d[0] else None} for s,d in sr[g].items() if d[0]>=20],
                     key=lambda x:-(x["pct"] or 0))
        coms=sorted([{"comarca":c,"n":d["n"],"pct":round(100*d["proc"]/d["n"]) if d["n"] else None,
                      "dm":med(d["dm"]) if len(d["dm"])>=15 else None,"pct_dm":round(100*len(d["dm"])/d["n"]) if d["n"] else None}
                     for c,d in com[g].items() if d["n"]>=8], key=lambda x:-x["n"])[:40]
        rs=sorted([{"reu":c,"n":d["n"],"pct":round(100*d["proc"]/d["n"]) if d["n"] else None,
                    "dm":med(d["dm"]) if len(d["dm"])>=10 else None}
                   for c,d in reu[g].items() if d["n"]>=5], key=lambda x:-x["n"])[:20]
        comp={}
        for s in cross[g]:
            lst=[{"comarca":c,"n":d["n"],"pct":round(100*d["proc"]/d["n"]) if d["n"] else None,
                  "dm":med(d["dm"]) if len(d["dm"])>=8 else None,"pct_dm":round(100*len(d["dm"])/d["n"]) if d["n"] else None}
                 for c,d in cross[g][s].items() if d["n"]>=8]
            if lst: comp[s]=sorted(lst,key=lambda x:-x["n"])[:25]
        return {"total":sum(d[0] for d in sr[g].values()),"dano_moral_por_area":dm_area,
                "exito_por_area":exito,"comarcas":coms,"reus":rs,"comparador":comp}
    out={"total":len(reg),"cidades":len(cidades),"n_juizes":len(juizes),"foros":dict(foros),
         "juizes":[{"juiz":j,"n":n} for j,n in juizes.most_common(40)],
         "por_foro":{g:por_foro(g) for g in G}}
    json.dump(out,open(OUT_STATS,"w",encoding="utf-8"),ensure_ascii=False,indent=1)

def main():
    reg=json.load(open(OUT_REG,encoding="utf-8")) if os.path.exists(OUT_REG) else []
    vistos=set(r["proc"] for r in reg if r.get("proc"))
    novos=0
    for setor,frase in TESES:
        for p in range(1,MAX_PAG+1):
            its=pega(frase,p)
            if not its: break
            for i in its:
                if i.get("tipoDocumento")!="Sentença": continue
                org=i.get("nomeOrgao")
                if not eh_1grau(org): continue
                pn=i.get("numeroprocessocommascara") or i.get("numero_processo")
                if not pn or pn in vistos: continue
                txt=i.get("texto") or ""
                res,venceu=resultado(txt); v=valor_cond(txt)
                rr=acha_reu(norm(txt[:1500]).upper()); c=comarca_de(org); j=juiz_de(txt)
                ft=foro(org); g="JUIZADO" if ft=="JUIZADO_ESPECIAL" else "COMUM"
                reg.append({"proc":pn,"s":setor,"c":c,"j":j,"r":rr,"fg":g,"res":res,
                            "v":v if venceu else None,"d":(i.get("data_disponibilizacao") or "")[:10],
                            "link":i.get("link"),"tese":frase,"em":ementa(txt)})
                vistos.add(pn); novos+=1
            time.sleep(0.15)
    reg.sort(key=lambda x:x.get("d") or "", reverse=True)
    json.dump(reg,open(OUT_REG,"w",encoding="utf-8"),ensure_ascii=False)
    rebuild_stats(reg)
    print(f"[atualizar_diario] janela {DI}..{DF} · novos: {novos} · total registros: {len(reg)}")

if __name__=="__main__": main()
