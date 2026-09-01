#!/usr/bin/env python3
"""
Segmentação FINA: por VARA (1º grau) e por TURMA + RELATOR + TIPO (2º grau).
1º grau (Varas de Consumo): duração ajuizamento->sentença, % procedência, dano moral, juízes, por vara.
2º grau (Turmas Recursais): por relator, distinguindo ACÓRDÃO (colegiado) x DECISÃO MONOCRÁTICA,
  duração até a decisão, % favorável. Salvador tem ~20 varas -> cada uma aparece separada.
Saída: vara_stats.json
"""
import json, re, statistics, os
from collections import defaultdict, Counter
from analise_dje import resultado, valor_cond, juiz_de
from analise_duracao import dur_meses

CIDADE_TAIL=re.compile(r"\b[Dd][EeAaOo]\s+([A-Za-zÀ-ú][A-Za-zÀ-ú'.\- ]+?)\s*$")
def split_orgao(o):
    """'CAPITAL > 16ª VARA DE RELAÇÕES DE CONSUMO' -> ('Salvador','16ª Vara ...').
    Sem '>' (ex.: '...Comerciais De Una') tenta a cidade no fim do nome."""
    if not o: return (None,None)
    s=o if isinstance(o,str) else (o.get("nome") or "")
    if ">" in s:
        com,vara=[p.strip() for p in s.split(">",1)]
    else:
        vara=s.strip(); com=""
        m=CIDADE_TAIL.search(vara)
        if m:
            cand=m.group(1).strip()
            # descarta caudas que não são cidade (ex.: 'Consumo', 'Trab')
            if cand.lower() not in ("consumo","consumidor","trab","fazenda pública","fazenda publica") and len(cand)>2:
                com=cand
    com={"CAPITAL":"Salvador"}.get(com.upper(), com.title()) if com else None
    return (com, vara.title() if vara else None)

COLEG=re.compile(r"\b(à\s+unanimidade|por\s+unanimidade|por\s+maioria|acordam\s+os|reuni[ru]|ac[oó]rd[aã]o)\b",re.I)
MONO =re.compile(r"(decis[aã]o\s+monocr[aá]tica|julg[ou]\s+monocr|monocraticamente|nego\s+seguimento\b)",re.I)
def tipo_decisao(t):
    if COLEG.search(t or ""): return "acordao"
    if MONO.search(t or ""):  return "monocratica"
    return "indef"

def med(a): return int(statistics.median(a)) if a else None
def medf(a): return round(statistics.median(a),1) if a else None

def carrega(files):
    seen=set()
    for fn in files:
        if not os.path.exists(fn): continue
        for l in open(fn,encoding="utf-8"):
            try: r=json.loads(l)
            except Exception: continue
            pn=r.get("numeroProcesso")
            if pn and pn in seen: continue
            if pn: seen.add(pn)
            yield r

# ---------- 1º grau: por VARA ----------
def primeiro_grau():
    V=defaultdict(lambda:{"proc":0,"improc":0,"dm":[],"dur":[],"juiz":Counter(),"ex":[]})
    for r in carrega(["corpus_censo.jsonl","corpus_dje.jsonl"]):
        com,vara=split_orgao(r.get("orgaoJulgador"))
        if not vara: continue
        key=(com or "?", vara)
        t=r.get("conteudo") or ""
        res,venceu=resultado(t)
        d=V[key]
        if venceu is True: d["proc"]+=1
        elif venceu is False: d["improc"]+=1
        if venceu:
            v=valor_cond(t)
            if v: d["dm"].append(v)
        m=dur_meses(r.get("numeroProcesso"), r.get("dataJulgamento"))
        if m is not None: d["dur"].append(m)
        j=juiz_de(t)
        if j: d["juiz"][j]+=1
        if len(d["ex"])<6 and r.get("numeroProcesso"): d["ex"].append(r["numeroProcesso"])
    out=[]
    for (com,vara),d in V.items():
        n=d["proc"]+d["improc"]
        if n<15: continue
        out.append({"comarca":com,"vara":vara,"n_merito":n,
                    "pct_proc":round(100*d["proc"]/n),"pct_improc":round(100*d["improc"]/n),
                    "dano_moral_mediana":med(d["dm"]),
                    "meses_mediana":medf(d["dur"]),"casos_com_data":len(d["dur"]),
                    "juizes":[j for j,_ in d["juiz"].most_common(3)],"ex":d["ex"]})
    out.sort(key=lambda x:(x["comarca"] or "zzz", -x["n_merito"]))
    return out

# ---------- 2º grau: por TURMA + RELATOR + TIPO ----------
def segundo_grau():
    R=defaultdict(lambda:{"fav":0,"unf":0,"acordao":0,"monocratica":0,"indef":0,"dur":[],"dm":[],"ex":[]})
    for r in carrega(["corpus_50k.jsonl","corpus_massa.jsonl"]):
        rel=(r.get("relator") or "").strip().title()
        if not rel: continue
        turma=(r.get("orgaoJulgador") or "")
        turma=turma if isinstance(turma,str) else (turma.get("nome") or "")
        key=(turma.title() or "Turma", rel)
        t=r.get("conteudo") or ""
        res,venceu=resultado(t)
        d=R[key]
        if venceu is True: d["fav"]+=1
        elif venceu is False: d["unf"]+=1
        d[tipo_decisao(t)]+=1
        m=dur_meses(r.get("numeroProcesso"), r.get("dataJulgamento"))
        if m is not None: d["dur"].append(m)
        if venceu:
            v=valor_cond(t)
            if v: d["dm"].append(v)
        if len(d["ex"])<6 and r.get("numeroProcesso"): d["ex"].append(r["numeroProcesso"])
    out=[]
    for (turma,rel),d in R.items():
        n=d["fav"]+d["unf"]
        if (d["acordao"]+d["monocratica"]+d["indef"])<20: continue
        tot_tipo=d["acordao"]+d["monocratica"]+d["indef"]
        out.append({"turma":turma,"relator":rel,"n":tot_tipo,
                    "pct_fav":round(100*d["fav"]/n) if n else None,
                    "acordao":d["acordao"],"monocratica":d["monocratica"],
                    "pct_monocratica":round(100*d["monocratica"]/tot_tipo) if tot_tipo else None,
                    "meses_mediana":medf(d["dur"]),"dano_moral_mediana":med(d["dm"]),"ex":d["ex"]})
    out.sort(key=lambda x:(x["turma"], -x["n"]))
    return out

def main():
    vg=primeiro_grau(); tg=segundo_grau()
    out={"fonte":"Varas de Consumo (1º grau, DJEN) e Turmas Recursais (2º grau). Duração: ano do nº CNJ x dataJulgamento.",
         "obs":"1º grau por VARA (Salvador tem ~20). 2º grau por RELATOR, distinguindo acórdão colegiado x decisão monocrática.",
         "varas_1grau":vg,"turmas_2grau":tg}
    json.dump(out,open("vara_stats.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
    sal=[v for v in vg if v["comarca"]=="Salvador"]
    print(f"1º GRAU: {len(vg)} varas ({len(sal)} em Salvador)")
    for v in sal[:22]:
        print(f"  {v['vara'][:38]:38} proc {v['pct_proc']:>3}%  {str(v['meses_mediana'])+'m':>6}  dm {v['dano_moral_mediana']}  (n={v['n_merito']})")
    print(f"\n2º GRAU: {len(tg)} relatores")
    for r in tg[:12]:
        print(f"  {r['relator'][:30]:30} {r['turma'][:16]:16} fav {r['pct_fav']:>3}%  mono {r['pct_monocratica']}%  {r['meses_mediana']}m (n={r['n']})")

if __name__=="__main__": main()
