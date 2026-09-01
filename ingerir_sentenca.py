#!/usr/bin/env python3
"""
INGESTOR de sentenças do PROJUDI (crowdsourcing) — resolve a ÍNTEGRA do Juizado.
O advogado (que tem acesso ao próprio processo) exporta a sentença e alimenta aqui;
a estruturação é a mesma da base (resultado, dano moral, réu, comarca, juiz, setor).
Aceita PDF (pypdf) ou .txt. Saída: corpus_projudi.jsonl (foro JUIZADO, entra na análise).

Uso:  python3 ingerir_sentenca.py sentenca1.pdf sentenca2.txt ...
"""
import sys, json, re, unicodedata
from analise_dje import resultado, valor_cond, juiz_de, acha_reu, norm

_SKW=[("AEREO",["voo","bagagem","aerea","overbooking","latam","gol linhas","azul linhas","aeroporto","anac"]),
 ("SAUDE",["plano de saude","operadora","ans","cirurgia","medicamento","unimed","hapvida","amil","cobertura","carencia"]),
 ("FRAUDE",["golpe","fraude","estelionato","transacao nao reconhecida","clonagem","engenharia social","pix"]),
 ("COELBA",["coelba","neoenergia","energia eletrica","fatura de energia","recuperacao de consumo","medidor"]),
 ("EMBASA",["embasa","agua e esgoto","fornecimento de agua","tarifa de esgoto"]),
 ("TELECOM",["telefonia","internet","banda larga","vivo","claro","tim ","oi movel"]),
 ("ECOMMERCE",["compra online","mercado livre","magazine luiza","americanas","shopee","produto com defeito","vicio do produto"]),
 ("APOSTAS",["aposta","casa de apostas"," bet ","bet365"]),
 ("FINANCEIRO",["banco","emprestimo","consignado","cartao de credito","negativacao","financiamento","tarifa bancaria","debito"])]
def setor_de(texto):
    n=unicodedata.normalize("NFKD",(texto or "").lower()).encode("ascii","ignore").decode()[:6000]
    best,sc="CONSUMO",0
    for s,kws in _SKW:
        c=sum(n.count(k) for k in kws)
        if c>sc: best,sc=s,c
    return best

RE_PROC=re.compile(r"\b(\d{7}-?\d{2}\.?\d{4}\.?8\.?05\.?\d{4})\b")
RE_COM=re.compile(r"COMARCA DE ([A-ZÁÂÃÉÊÍÓÔÕÚÇ'’ ]{3,30}?)(?=\s*(?:[/\-–,.\n]|SENTEN|PROCESSO|AUTOS|VARA|JUIZ|ESTADO|$))", re.I)

def ler(path):
    if path.lower().endswith(".pdf"):
        from pypdf import PdfReader
        return "\n".join((p.extract_text() or "") for p in PdfReader(path).pages)
    return open(path, encoding="utf-8", errors="replace").read()

def main():
    files=sys.argv[1:]
    if not files:
        print("uso: python3 ingerir_sentenca.py <arquivo.pdf|.txt> [...]"); return
    fh=open("corpus_projudi.jsonl","a",encoding="utf-8"); ok=0
    for f in files:
        try: t=ler(f)
        except Exception as e: print(f"  {f}: erro ao ler ({e})"); continue
        if len((t or "").strip())<300:
            print(f"  {f}: texto curto/ilegível — pulado (PDF pode ser imagem escaneada; precisa OCR)"); continue
        res,venceu=resultado(t)
        mp=RE_PROC.search(t); mc=RE_COM.search(t)
        rec={"numeroProcesso":(mp.group(1) if mp else f),"tribunal":"TJBA","fonte":"PROJUDI-crowd",
             "instancia":"1G","foro_tipo":"JUIZADO_ESPECIAL","setor":setor_de(t),
             "orgaoJulgador":"JUIZADO ESPECIAL"+(f" DA COMARCA DE {mc.group(1).strip().upper()}" if mc else ""),
             "comarca":(mc.group(1).strip().title() if mc else None),"juiz":juiz_de(t),
             "resultado":res,"valor_dano_moral":valor_cond(t) if venceu else None,
             "reu":acha_reu(norm(t[:1500]).upper()),"conteudo":t}
        fh.write(json.dumps(rec,ensure_ascii=False)+"\n"); ok+=1
        print(f"  {f}: setor={rec['setor']} · {res} · dano moral={rec['valor_dano_moral']} · réu={rec['reu']} · comarca={rec['comarca']}")
    fh.close()
    print(f"\n{ok} sentença(s) ingerida(s) -> corpus_projudi.jsonl (rode analise_dje.py p/ agregar)")

if __name__=="__main__": main()
