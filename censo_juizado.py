#!/usr/bin/env python3
"""
CENSO COMPLETO dos Juizados da BA (Datajud/CNJ) — por PROCEDÊNCIA, TESE e COMARCA,
com AMOSTRA DE NÚMEROS DE PROCESSO pra validação humana pelo usuário.
Usa agregações (contagem real, sem paginar milhões) + top_hits (exemplos de processo).
Resultado por código oficial de movimento: 219 Procedência, 221 Parcial, 220 Improcedência.
Comarca pelo IBGE (nome oficial). Saída: censo_juizado.json
"""
import urllib.request, json, sys, gzip
EP="https://api-publica.datajud.cnj.jus.br/api_publica_tjba/_search"
KEY="APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
COD={"proc":219,"parc":221,"improc":220}
NEX=6   # exemplos de processo por bucket
# 3 segmentos (Justiça Comum vem do DJEN, separado). Cível = Cível SEM órgão Fazenda.
SEGMENTOS={
 "CIVEL":{"must":[{"match_phrase":{"classe.nome":"Procedimento do Juizado Especial Cível"}}],
          "must_not":[{"match":{"orgaoJulgador.nome":"Fazenda"}}]},
 "FAZENDA":{"must":[{"match_phrase":{"classe.nome":"Procedimento do Juizado Especial da Fazenda Pública"}}]},
}

def q(body):
    r=urllib.request.Request(EP,data=json.dumps(body).encode(),method="POST",
        headers={"Authorization":KEY,"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(r,timeout=90).read())

def ibge_nomes():
    try:
        r=urllib.request.Request("https://servicodados.ibge.gov.br/api/v1/localidades/estados/29/municipios",
            headers={"accept":"application/json","Accept-Encoding":"identity"})
        data=urllib.request.urlopen(r,timeout=40).read()
        if data[:2]==b"\x1f\x8b": data=gzip.decompress(data)
        return {int(m["id"]):m["nome"] for m in json.loads(data.decode("utf-8"))}
    except Exception as e:
        print("falha IBGE:",e,file=sys.stderr); return {}

def agg_por(seg, campo, cod, size):
    """conta processos do segmento com movimento=cod, agrupado por campo, com exemplos de processo."""
    must=list(SEGMENTOS[seg]["must"])+[{"match":{"movimentos.codigo":cod}}]
    query={"bool":{"must":must}}
    if SEGMENTOS[seg].get("must_not"): query["bool"]["must_not"]=SEGMENTOS[seg]["must_not"]
    b={"size":0,"query":query,
       "aggs":{"g":{"terms":{"field":campo,"size":size},
                    "aggs":{"ex":{"top_hits":{"size":NEX,"_source":["numeroProcesso"]}}}}}}
    out={}
    for x in q(b)["aggregations"]["g"]["buckets"]:
        procs=[h["_source"]["numeroProcesso"] for h in x["ex"]["hits"]["hits"]]
        out[x["key"]]={"n":x["doc_count"],"ex":procs}
    return out

def montar(seg, campo, size, nomemap=None):
    p=agg_por(seg,campo,COD["proc"],size); a=agg_por(seg,campo,COD["parc"],size); i=agg_por(seg,campo,COD["improc"],size)
    chaves=set(p)|set(a)|set(i); linhas=[]
    for k in chaves:
        np=p.get(k,{}).get("n",0); na=a.get(k,{}).get("n",0); ni=i.get(k,{}).get("n",0)
        fav=np+na; tot=fav+ni
        if tot<30: continue
        nome=nomemap.get(int(k),str(k)) if nomemap else k
        linhas.append({"nome":nome,"n":tot,"procedente":np,"parcial":na,"improcedente":ni,
            "pct_fav":round(100*fav/tot),
            "ex_favoravel":(p.get(k,{}).get("ex",[])+a.get(k,{}).get("ex",[]))[:NEX],
            "ex_improcedente":i.get(k,{}).get("ex",[])[:NEX]})
    linhas.sort(key=lambda x:-x["n"])
    return linhas

def main():
    nomes=ibge_nomes()
    out={"fonte":"Datajud/CNJ (censo por agregação)",
         "obs":"procedência por código oficial de movimento (219/221 vs 220); comarca por IBGE; exemplos de nº de processo p/ validação. Cível exclui órgãos da Fazenda.",
         "segmentos":{}}
    for seg,rotulo in [("CIVEL","Juizado Especial Cível"),("FAZENDA","Juizado da Fazenda Pública")]:
        print(f"censo {rotulo}...",file=sys.stderr)
        teses=montar(seg,"assuntos.nome.keyword",60)
        comarcas=montar(seg,"orgaoJulgador.codigoMunicipioIBGE",600,nomes)
        tot=sum(c["n"] for c in comarcas); fav=sum(c["procedente"]+c["parcial"] for c in comarcas)
        out["segmentos"][seg]={"rotulo":rotulo,"total":tot,"pct_fav_geral":round(100*fav/tot) if tot else None,
                               "por_tese":teses,"comarcas":comarcas}
        print("  {}: {} decisões · {} teses · {} comarcas · favorável {}%".format(rotulo,tot,len(teses),len(comarcas),out["segmentos"][seg]["pct_fav_geral"]))
        for t in teses[:5]: print("     {:40} {}% (n={})".format(t["nome"][:40],t["pct_fav"],t["n"]))
    json.dump(out,open("censo_juizado.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)

if __name__=="__main__": main()
