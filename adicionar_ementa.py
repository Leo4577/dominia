#!/usr/bin/env python3
"""
Adiciona a EMENTA (resumo/dispositivo) a cada registro de registros_dje.json,
extraindo do texto das sentenças no corpus (corpus_censo + corpus_dje).
Assim a aba Decisões e a auditoria mostram o QUE foi decidido, não só o nº.
Saída: reescreve registros_dje.json com o campo "em".
"""
import json, re, os

# --- privacidade: mascara nome de PESSOA física na ementa (mantém réu-empresa) ---
SOBRENOMES=set("SILVA SANTOS SOUZA SOUSA OLIVEIRA PEREIRA LIMA CARVALHO FERREIRA RODRIGUES ALMEIDA COSTA GOMES MARTINS ARAUJO ARAÚJO RIBEIRO MELO NASCIMENTO SANTANA JESUS CONCEICAO CONCEIÇÃO CRUZ REIS BARBOSA ROCHA DIAS MOREIRA NUNES MENDES FREITAS CARNEIRO ANDRADE CARDOSO TEIXEIRA MACHADO VIEIRA MONTEIRO CAVALCANTE CAVALCANTI CAMPOS BATISTA MIRANDA CORREIA PINTO RAMOS AMARAL LOPES FONSECA BORGES GONCALVES GONÇALVES FRANCA FRANÇA XAVIER MAIA AGUIAR MATOS FARIAS SALES NOGUEIRA".split())
NAME_RUN=re.compile(r"\b([A-ZÀ-Ú]{2,}(?:\s+(?:DA|DE|DO|DAS|DOS|E|[A-ZÀ-Ú]{2,})){1,6})\b")
def mascara_nome(t):
    if not t: return t
    def repl(m):
        raw=m.group(1); allt=raw.split()
        core=[w for w in allt if w not in ("DA","DE","DO","DAS","DOS","E")]
        has_part=any(w in ("DA","DE","DO","DAS","DOS") for w in allt)
        if len(core)>=2 and (any(w in SOBRENOMES for w in core) or (has_part and len(core)>=3)):
            return core[0][0]+". [nome preservado]"
        return raw
    return NAME_RUN.sub(repl,t)

DISP=re.compile(r"(ANTE O EXPOSTO|DIANTE DO EXPOSTO|ISTO POSTO|POSTO ISSO|PELO EXPOSTO|Ante o exposto|Diante do exposto|Isto posto|Posto isso|Pelo exposto)")
JULGO=re.compile(r"\bJULGO\b", re.I)
INICIO=re.compile(r"(Trata-se|Cuida-se|Vistos[,.]|Dispensad[oa] o relat[óo]rio|RELAT[ÓO]RIO)")
CABEC=re.compile(r"^(PODER JUDICI|TRIBUNAL DE JUST|ID do Documento|Processo:)", re.I)
def ementa(t):
    t=re.sub(r"\s+"," ",t or "").strip()
    if not t: return None
    m=DISP.search(t)
    if m: seg=t[m.start():m.start()+360]
    else:
        m2=JULGO.search(t)
        if m2: seg=t[max(0,m2.start()-24):m2.start()+320]
        else:
            m3=INICIO.search(t); seg=t[m3.start():m3.start()+340] if m3 else t[400:760]
    seg=seg.strip()
    if CABEC.search(seg):                      # caiu no cabeçalho -> pula o bloco de metadados
        m3=INICIO.search(t) or DISP.search(t) or JULGO.search(t)
        seg=(t[m3.start():m3.start()+340] if m3 else t[400:760]).strip()
    return mascara_nome(seg[:360]) or None

def build_map(files):
    mp={}
    for fn in files:
        if not os.path.exists(fn): continue
        for l in open(fn,encoding="utf-8"):
            try: r=json.loads(l)
            except Exception: continue
            pn=r.get("numeroProcesso")
            if pn and pn not in mp:
                e=ementa(r.get("conteudo"))
                if e: mp[pn]=e
    return mp

def main():
    reg=json.load(open("registros_dje.json",encoding="utf-8"))
    print(f"registros: {len(reg)} — lendo corpus p/ ementas...")
    mp=build_map(["corpus_dje.jsonl","corpus_censo.jsonl"])
    print(f"ementas encontradas: {len(mp)}")
    n=0
    for r in reg:
        e=mp.get(r.get("proc"))
        if e: r["em"]=e; n+=1
    json.dump(reg,open("registros_dje.json","w",encoding="utf-8"),ensure_ascii=False)
    print(f"registros com ementa: {n}/{len(reg)}")

if __name__=="__main__": main()
