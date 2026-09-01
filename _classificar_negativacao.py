#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera estruturado_negativacao.jsonl a partir da classificacao manual do inteiro teor."""
import json

RAW = "raw_negativacao.jsonl"
OUT = "estruturado_negativacao.jsonl"

# Classificacao manual (baseada SOMENTE no texto do inteiro teor lido).
# Chave = numeroProcesso.  Decisoes de merito sobre negativacao/inscricao indevida.
CLASS = {
    "0159789-46.2025.8.05.0001": {  # Bradesco
        "reu": "BRADESCO",
        "micro_tese": "NEGATIVACAO_COM_DIVIDA_PREEXISTENTE",
        "resultado_consumidor": "PARCIAL",
        "dano_moral_concedido": False, "dano_moral_valor": 0,
        "fundamentos": ["Sumula 385 STJ - negativacao preexistente legitima afasta dano moral",
                        "debito declarado inexistente mas sem indenizacao (so cancelamento)"],
        "prova_decisiva": ["certidao com negativacao preexistente (MG-MBE/Brasil Card, 16/12/2024)"],
        "comarca": "Salvador", "vara_origem": ""},
    "0165461-35.2025.8.05.0001": {  # Itau
        "reu": "ITAU",
        "micro_tese": "NEGATIVACAO_INDEVIDA_SEM_DIVIDA",
        "resultado_consumidor": "PARCIAL",
        "dano_moral_concedido": True, "dano_moral_valor": 3000,
        "fundamentos": ["non reformatio in pejus (recurso exclusivo do autor)",
                        "contratacao regular comprovada (documento de recebimento do cartao)",
                        "art. 373, II, CPC - fato desconstitutivo comprovado pela re"],
        "prova_decisiva": ["documento assinado de recebimento do cartao (ev. 12.8)"],
        "comarca": "Salvador", "vara_origem": ""},
    "0101637-05.2025.8.05.0001": {  # Sem Parar Sociedade de Credito Direto
        "reu": "SEM PARAR",
        "micro_tese": "NEGATIVACAO_INDEVIDA_SEM_DIVIDA",
        "resultado_consumidor": "GANHOU",
        "dano_moral_concedido": True, "dano_moral_valor": 6000,
        "fundamentos": ["responsabilidade objetiva art. 14 CDC",
                        "re nao comprovou regularidade da contratacao/debito (art. 373, II, CPC)",
                        "dano moral configurado"],
        "prova_decisiva": ["ausencia de prova da contratacao/regularidade do debito pela re"],
        "comarca": "Salvador", "vara_origem": ""},
    "0190065-60.2025.8.05.0001": {  # Sem Parar Inst. Pagamento
        "reu": "SEM PARAR",
        "micro_tese": "OUTRO",
        "resultado_consumidor": "PERDEU",
        "dano_moral_concedido": False, "dano_moral_valor": 0,
        "fundamentos": ["negativacao devida - exercicio regular de direito",
                        "Sumula 10 TU/TJBA - relacao juridica comprovada por qualquer meio",
                        "ausencia de prova de pagamento pelo autor"],
        "prova_decisiva": ["comprovacao da relacao juridica e do inadimplemento pela re"],
        "comarca": "Salvador", "vara_origem": ""},
    "0137300-15.2025.8.05.0001": {  # Banco Original
        "reu": "BANCO ORIGINAL",
        "micro_tese": "NEGATIVACAO_INDEVIDA_SEM_DIVIDA",
        "resultado_consumidor": "PARCIAL",
        "dano_moral_concedido": False, "dano_moral_valor": 0,
        "fundamentos": ["debito declarado inexistente (re nao comprovou legalidade)",
                        "negativacao nao provada por certidao oficial - dano moral afastado",
                        "art. 373, I, CPC - onus do autor de provar a inscricao"],
        "prova_decisiva": ["ausencia de certidao oficial SPC/Serasa/CDL (extrato nao oficial inidoneo)"],
        "comarca": "Salvador", "vara_origem": ""},
    "0165562-72.2025.8.05.0001": {  # contratacao nao reconhecida (3a TR)
        "reu": "NAO IDENTIFICADO",
        "micro_tese": "NEGATIVACAO_INDEVIDA_SEM_DIVIDA",
        "resultado_consumidor": "GANHOU",
        "dano_moral_concedido": True, "dano_moral_valor": 6000,
        "fundamentos": ["dano moral in re ipsa",
                        "responsabilidade objetiva art. 14 CDC",
                        "re nao comprovou a origem da divida/contrato (art. 373, II, CPC)"],
        "prova_decisiva": ["re nao juntou contrato; contestacao generica sem prova"],
        "comarca": "Salvador", "vara_origem": ""},
    "0034967-82.2025.8.05.0001": {  # Itau
        "reu": "ITAU",
        "micro_tese": "OUTRO",
        "resultado_consumidor": "PERDEU",
        "dano_moral_concedido": False, "dano_moral_valor": 0,
        "fundamentos": ["debito existente comprovado - inscricao e exercicio regular de direito",
                        "Sumula 359 STJ - notificacao previa e do orgao mantenedor",
                        "art. 373, I, CPC - autor nao comprovou quitacao"],
        "prova_decisiva": ["solicitacao de cartao, historico de uso, pagamentos e inadimplencia (ev. 10)"],
        "comarca": "Salvador", "vara_origem": "11a VSJE do Consumidor"},
    "0153868-09.2025.8.05.0001": {  # Client Co
        "reu": "CLIENT CO",
        "micro_tese": "NEGATIVACAO_INDEVIDA_SEM_DIVIDA",
        "resultado_consumidor": "PARCIAL",
        "dano_moral_concedido": False, "dano_moral_valor": 0,
        "fundamentos": ["debito declarado inexistente (falha na prestacao do servico)",
                        "negativacao nao comprovada - meras cobrancas nao geram dano moral",
                        "mero aborrecimento nao indenizavel"],
        "prova_decisiva": ["certidao do ev. 1 nao e de orgao arquivista oficial"],
        "comarca": "Salvador", "vara_origem": "4a VSJE do Consumidor"},
    "0161133-62.2025.8.05.0001": {  # Bradesco
        "reu": "BRADESCO",
        "micro_tese": "OUTRO",
        "resultado_consumidor": "PERDEU",
        "dano_moral_concedido": False, "dano_moral_valor": 0,
        "fundamentos": ["debito comprovado - negativacao devida (exercicio regular de direito)",
                        "Sumula 10 TU/TJBA - relacao comprovada por qualquer meio",
                        "litigancia de ma-fe configurada (art. 81 CPC)"],
        "prova_decisiva": ["documentos da relacao juridica e da divida (ev. 17); autor nao provou pagamento"],
        "comarca": "Salvador", "vara_origem": ""},
    "0147066-92.2025.8.05.0001": {  # Getnet
        "reu": "GETNET",
        "micro_tese": "NEGATIVACAO_INDEVIDA_SEM_DIVIDA",
        "resultado_consumidor": "PARCIAL",
        "dano_moral_concedido": True, "dano_moral_valor": 3000,
        "fundamentos": ["certidao de plataforma privada (CredNet) nao comprova negativacao",
                        "non reformatio in pejus (recurso exclusivo do autor)",
                        "art. 373, I, CPC - onus do autor"],
        "prova_decisiva": ["certidao CredNet (nao oficial) - inapta a provar inscricao"],
        "comarca": "Salvador", "vara_origem": ""},
    "0008341-11.2025.8.05.0103": {  # Bradesco - Sumula 385 nuance
        "reu": "BRADESCO",
        "micro_tese": "NEGATIVACAO_COM_DIVIDA_PREEXISTENTE",
        "resultado_consumidor": "GANHOU",
        "dano_moral_concedido": True, "dano_moral_valor": 4000,
        "fundamentos": ["Sumula 385 STJ afastada - re nao comprovou legitimidade das inscricoes preexistentes",
                        "preclusao - documentos juntados so em fase recursal (art. 434 CPC)",
                        "historico crediticio usado apenas para dosimetria (reducao de 8000 para 4000)"],
        "prova_decisiva": ["consulta a orgaos de credito mostrando anotacoes anteriores (Santander) impugnadas pelo consumidor"],
        "comarca": "", "vara_origem": ""},
    "0134823-19.2025.8.05.0001": {  # PicPay Bank
        "reu": "PICPAY",
        "micro_tese": "NEGATIVACAO_INDEVIDA_SEM_DIVIDA",
        "resultado_consumidor": "GANHOU",
        "dano_moral_concedido": True, "dano_moral_valor": 10000,
        "fundamentos": ["dano moral in re ipsa - negativacao por divida nao reconhecida",
                        "revelia (re validamente citada nao contestou)",
                        "re nao comprovou contratacao (art. 373, II, CPC); majoracao de 5000 para 10000"],
        "prova_decisiva": ["revelia; ausencia de prova da contratacao; autora sem outras inscricoes"],
        "comarca": "Salvador", "vara_origem": ""},
    "0194100-63.2025.8.05.0001": {  # Banco do Brasil
        "reu": "BANCO DO BRASIL",
        "micro_tese": "NEGATIVACAO_INDEVIDA_SEM_DIVIDA",
        "resultado_consumidor": "GANHOU",
        "dano_moral_concedido": True, "dano_moral_valor": None,
        "fundamentos": ["responsabilidade objetiva art. 14 CDC",
                        "re nao comprovou a contratacao (art. 373, II, CPC)",
                        "inscricao posterior nao atrai Sumula 385 (serve so de diretriz p/ quantum)"],
        "prova_decisiva": ["ausencia de prova da contratacao pela re; extrato com inscricoes posteriores"],
        "comarca": "Salvador", "vara_origem": ""},
    "0168371-35.2025.8.05.0001": {  # Sem Parar Sociedade de Credito
        "reu": "SEM PARAR",
        "micro_tese": "NEGATIVACAO_INDEVIDA_SEM_DIVIDA",
        "resultado_consumidor": "GANHOU",
        "dano_moral_concedido": True, "dano_moral_valor": 5000,
        "fundamentos": ["dano moral in re ipsa (extrato oficial comprova inscricao)",
                        "re nao comprovou o debito (art. 373, II, CPC); preclusao de docs recursais",
                        "Sumula 359 STJ - notificacao e do orgao mantenedor; negativacoes posteriores so afetam quantum"],
        "prova_decisiva": ["extrato de orgao oficial juntado pelo autor (ev. 1); ausencia de prova do debito pela re"],
        "comarca": "Salvador", "vara_origem": "12a VSJE do Consumidor"},
    "0185942-19.2025.8.05.0001": {  # falha nos servicos (3a TR)
        "reu": "NAO IDENTIFICADO",
        "micro_tese": "NEGATIVACAO_INDEVIDA_SEM_DIVIDA",
        "resultado_consumidor": "GANHOU",
        "dano_moral_concedido": True, "dano_moral_valor": 6000,
        "fundamentos": ["dano moral in re ipsa - inscricao ilegal",
                        "re nao comprovou legalidade do debito (art. 373, II, CPC)",
                        "ausencia de documentos de validacao do contrato"],
        "prova_decisiva": ["comprovante de negativacao valido (ev. 15); ausencia de contrato/cessao de credito"],
        "comarca": "Salvador", "vara_origem": ""},
}

# Decisoes PULADAS (nao-merito ou fora do escopo), para registro:
# 0010209-77.2025.8.05.0150 - Embargos de Declaracao (nao merito)
# 0002659-61.2025.8.05.0043 - Embargos de Declaracao (nao merito)
# 0067382-21.2025.8.05.0001 - hospital/plano de saude; negativacao nao provada (fora inst. financeira)
# 0026012-19.2025.8.05.0080 - FIDC; negativacao nao provada (mera cobranca)
# 0133381-18.2025.8.05.0001 - Telefonica; Serasa Limpa Nome (nao e negativacao)
# 0060248-40.2025.8.05.0001 - GEAP plano de saude (so danos materiais)
# 0151934-16.2025.8.05.0001 - Editora Educacional (debito de curso comprovado; nao inst. financeira)

raw = {}
with open(RAW, encoding="utf-8") as f:
    for line in f:
        d = json.loads(line)
        raw[d["numeroProcesso"]] = d

n = 0
with open(OUT, "w", encoding="utf-8") as out:
    for num, c in CLASS.items():
        d = raw[num]
        rec = {
            "numeroProcesso": num,
            "reu": c["reu"],
            "orgaoJulgador": d.get("orgaoJulgador", ""),
            "relator": d.get("relator", ""),
            "dataJulgamento": d.get("dataJulgamento", ""),
            "classe": d.get("classe", ""),
            "tese_grupo": "FINANCEIRO",
            "micro_tese": c["micro_tese"],
            "resultado_consumidor": c["resultado_consumidor"],
            "dano_moral_concedido": c["dano_moral_concedido"],
            "dano_moral_valor": c["dano_moral_valor"],
            "fundamentos": c["fundamentos"],
            "prova_decisiva": c["prova_decisiva"],
            "comarca": c["comarca"],
            "vara_origem": c["vara_origem"],
        }
        out.write(json.dumps(rec, ensure_ascii=False) + "\n")
        n += 1

print(f"OK: {n} decisoes de merito classificadas em {OUT}")

# Resumo
fav = sum(1 for c in CLASS.values() if c["resultado_consumidor"] in ("GANHOU", "PARCIAL"))
ganhou = sum(1 for c in CLASS.values() if c["resultado_consumidor"] == "GANHOU")
parcial = sum(1 for c in CLASS.values() if c["resultado_consumidor"] == "PARCIAL")
perdeu = sum(1 for c in CLASS.values() if c["resultado_consumidor"] == "PERDEU")
valores = [c["dano_moral_valor"] for c in CLASS.values() if c["dano_moral_concedido"] and c["dano_moral_valor"]]
print(f"Favoravel (ganhou+parcial): {fav}/{n} = {100*fav/n:.0f}%")
print(f"  GANHOU={ganhou} PARCIAL={parcial} PERDEU={perdeu}")
print(f"Dano moral concedido em: {sum(1 for c in CLASS.values() if c['dano_moral_concedido'])} casos")
print(f"Valores dano moral (conhecidos): {sorted(valores)} -> faixa R${min(valores)}-R${max(valores)}")
