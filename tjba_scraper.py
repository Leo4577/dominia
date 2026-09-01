#!/usr/bin/env python3
"""
Scraper piloto — Jurimetria JUZIA
Fonte: API GraphQL do portal de jurisprudencia do TJBA
Endpoint: https://jurisprudenciaws.tjba.jus.br/graphql

Coleta acordaos das Turmas Recursais (Juizados Especiais) por tese/assunto,
incluindo o INTEIRO TEOR (campo 'conteudo'), e salva em JSONL.

Uso:
    python3 tjba_scraper.py "bagagem extraviada" --max 30
    python3 tjba_scraper.py --tese-file teses.txt --max 100
"""
import json, time, argparse, sys, urllib.request, urllib.error, re, os

ENDPOINT = "https://jurisprudenciaws.tjba.jus.br/graphql"
FORO_COMUM = False  # False=Juizado (Turmas Recursais) / True=Justiça Comum (Câmaras Cíveis)

QUERY = ("query filter($decisaoFilter: DecisaoFilter!,$pageNumber: Int!,$itemsPerPage: Int!){"
         " filter(decisaoFilter:$decisaoFilter,pageNumber:$pageNumber,itemsPerPage:$itemsPerPage){"
         " decisoes{ numeroProcesso tipoDecisao dataPublicacao dataJulgamento"
         " relator{ nome } orgaoJulgador{ nome } classe{ descricao } ementa conteudo }"
         " pageCount itemCount } }")

def build_filter(assunto):
    return {
        "assunto": assunto,          # use aspas na string p/ frase exata: '"bagagem extraviada"'
        "numeroRecurso": "",
        "orgaos": [], "relatores": [], "classes": [],
        "dataInicial": None, "dataFinal": None,
        "segundoGrau": FORO_COMUM,
        "turmasRecursais": not FORO_COMUM,
        "tipoAcordaos": True,
        "tipoDecisoesMonocraticas": True,
        "ordenadoPor": "dataPublicacao",
    }

def post(variables, retries=3):
    body = json.dumps({"query": QUERY, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(ENDPOINT, data=body, method="POST", headers={
        "content-type": "application/json",
        "origin": "https://jurisprudencia.tjba.jus.br",
        "referer": "https://jurisprudencia.tjba.jus.br/",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) juzia-pesquisa/0.1",
    })
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read().decode("utf-8"))
            if data.get("errors"):
                raise RuntimeError(data["errors"][0].get("message"))
            return data["data"]["filter"]
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(2 * (attempt + 1))

# ---- extracao leve de metadados do inteiro teor (heuristica, refinada depois por IA) ----
RE_ORIGEM = re.compile(r"ORIGEM:\s*(.+?)(?:\s{2,}|RECOR|EMENTA|\n|RELAT)", re.I)
RE_COMARCA = re.compile(r"(\d+[ªa]?\s*VARA[^\n]{0,60}?)(?:\s{2,}|-\s|\n)", re.I)
RESULT_WORDS = [
    ("PROVIMENTO_NEGADO", r"nega[r]?-?se\s+provimento|nego\s+provimento|recurso\s+improvido|improvido\s+o\s+recurso|negar\s+provimento"),
    ("PROVIMENTO_DADO",   r"d[aá]-?se\s+provimento|dou\s+provimento|recurso\s+provido|provido\s+o\s+recurso|dar\s+provimento"),
    ("PARCIAL",           r"parcial\s+provimento"),
    ("SENTENCA_MANTIDA",  r"mant[eê]m-?se\s+a\s+senten[çc]a|senten[çc]a\s+mantida|confirma[r]?\s+a\s+senten[çc]a"),
]
def extract_meta(conteudo):
    txt = re.sub(r"\s+", " ", conteudo or "")
    origem = None
    m = RE_ORIGEM.search(txt) or RE_COMARCA.search(txt)
    if m:
        origem = m.group(1).strip()[:80]
    dispositivo = None
    low = txt.lower()
    for label, pat in RESULT_WORDS:
        if re.search(pat, low):
            dispositivo = label
            break
    return {"origem_1grau": origem, "dispositivo_recurso": dispositivo}

def scrape(assunto, max_items, out_fh, per_page=10, sleep=1.0):
    seen = set()
    page, got = 1, 0
    first = post({"decisaoFilter": build_filter(assunto), "pageNumber": 1, "itemsPerPage": per_page})
    total = first["itemCount"]
    print(f"  [{assunto}] itemCount={total} pageCount={first['pageCount']}", file=sys.stderr)
    while got < max_items:
        data = first if page == 1 else post(
            {"decisaoFilter": build_filter(assunto), "pageNumber": page, "itemsPerPage": per_page})
        decs = data.get("decisoes") or []
        if not decs:
            break
        for d in decs:
            proc = d.get("numeroProcesso")
            if proc in seen:
                continue
            seen.add(proc)
            rec = {
                "assunto_busca": assunto,
                "numeroProcesso": proc,
                "tipoDecisao": d.get("tipoDecisao"),
                "orgaoJulgador": (d.get("orgaoJulgador") or {}).get("nome"),
                "relator": (d.get("relator") or {}).get("nome"),
                "classe": (d.get("classe") or {}).get("descricao"),
                "dataPublicacao": d.get("dataPublicacao"),
                "dataJulgamento": d.get("dataJulgamento"),
                "ementa": (d.get("ementa") or "").strip(),
                "conteudo": d.get("conteudo") or "",
            }
            rec.update(extract_meta(rec["conteudo"]))
            out_fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            got += 1
            if got >= max_items:
                break
        page += 1
        time.sleep(sleep)
    return got

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tese", nargs="?", help='ex: "bagagem extraviada" (use aspas internas p/ frase exata)')
    ap.add_argument("--tese-file")
    ap.add_argument("--max", type=int, default=30)
    ap.add_argument("--out", default="decisoes_tjba.jsonl")
    ap.add_argument("--phrase", action="store_true", help="envolve a tese em aspas (frase exata)")
    ap.add_argument("--comum", action="store_true", help="busca na Justiça Comum (Câmaras Cíveis) em vez do Juizado")
    args = ap.parse_args()

    global FORO_COMUM
    FORO_COMUM = args.comum
    teses = []
    if args.tese_file:
        teses = [l.strip() for l in open(args.tese_file, encoding="utf-8") if l.strip()]
    elif args.tese:
        teses = [args.tese]
    else:
        ap.error("informe uma tese ou --tese-file")

    total = 0
    with open(args.out, "w", encoding="utf-8") as fh:
        for t in teses:
            q = f'"{t}"' if args.phrase else t
            total += scrape(q, args.max, fh)
    print(f"OK: {total} decisoes salvas em {args.out}", file=sys.stderr)

if __name__ == "__main__":
    main()
