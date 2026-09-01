#!/usr/bin/env python3
"""
DURAÇÃO média do processo (ajuizamento -> decisão), por COMARCA de Juizado e por RELATOR.
Ano de ajuizamento vem do próprio nº CNJ; data da decisão = dataJulgamento.
Ajuda o advogado a escolher onde ajuizar (comarca mais rápida). Saída: duracao_stats.json
"""
import json, re, statistics, os
from datetime import date
from collections import defaultdict

ANO=re.compile(r"\.(\d{4})\.")
def ajuiz_ano(num):
    m=ANO.search(num or "")
    return int(m.group(1)) if m else None
def julg_date(s):
    try: y,mo,d=map(int,s.split("-")[:3]); return date(y,mo,d)
    except Exception: return None
def dur_meses(num, julg):
    a=ajuiz_ano(num); jd=julg_date(julg)
    if not a or not jd: return None
    dias=(jd-date(a,7,1)).days           # ajuizamento estimado no meio do ano de registro
    if dias<0 or dias>3650: return None  # descarta ruído (>10 anos ou negativo)
    return round(dias/30.44,1)
def comarca_de_str(o):
    if not o: return None
    s=o if isinstance(o,str) else (o.get("nome") or "")
    c=s.split(">")[0].strip().upper()
    return {"CAPITAL":"Salvador"}.get(c, c.title()) if c else None

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

def agrega(rows, chave_fn, minn):
    D=defaultdict(list); EX=defaultdict(list)
    for r in rows:
        k=chave_fn(r)
        if not k: continue
        m=dur_meses(r.get("numeroProcesso"), r.get("dataJulgamento"))
        if m is None: continue
        D[k].append(m)
        if len(EX[k])<5: EX[k].append(r.get("numeroProcesso"))
    out=[]
    for k,v in D.items():
        if len(v)<minn: continue
        v.sort()
        out.append({"chave":k,"n":len(v),"meses_mediana":round(statistics.median(v),1),
                    "meses_p25":round(v[len(v)//4],1),"meses_p75":round(v[len(v)*3//4],1),"ex":EX[k]})
    out.sort(key=lambda x:x["meses_mediana"])
    return out

def main():
    comarcas=agrega(carrega(["corpus_censo.jsonl","corpus_dje.jsonl"]),
                    lambda r:comarca_de_str(r.get("orgaoJulgador")), 25)
    relatores=agrega(carrega(["corpus_50k.jsonl","corpus_massa.jsonl"]),
                     lambda r:(r.get("relator") or "").strip().title() or None, 25)
    out={"fonte":"nº CNJ (ano de ajuizamento) x dataJulgamento",
         "obs":"Duração estimada até a decisão. Comarca = tempo até a sentença de 1º grau (Varas de Consumo); Relator = tempo até o acórdão da Turma. Ajuizamento estimado no meio do ano de registro.",
         "comarcas":comarcas,"relatores":relatores}
    json.dump(out,open("duracao_stats.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
    print(f"COMARCAS (mais rápidas primeiro): {len(comarcas)}")
    for c in comarcas[:12]: print(f"  {c['chave'][:26]:26} {c['meses_mediana']:>5} meses  (n={c['n']}, p25-p75 {c['meses_p25']}-{c['meses_p75']})")
    print(f"RELATORES: {len(relatores)}")
    for c in relatores[:8]: print(f"  {c['chave'][:30]:30} {c['meses_mediana']:>5} meses (n={c['n']})")

if __name__=="__main__": main()
