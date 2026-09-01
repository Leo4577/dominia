#!/usr/bin/env python3
"""
ALERTAS DE SUSPENSÃO — teses repetitivas de consumidor com processamento SUSPENSO
(Tema Repetitivo STJ / IRDR / IAC). Conteúdo curado e datado; SUSPENSÃO É TEMPORÁRIA —
revisar periodicamente (cai quando o tribunal julga o mérito). Fontes nas notas.
"""
SUSPENSOES = [
 {
  "tese": "Cartão de crédito consignado (RMC / RCC)",
  "instrumento": "Tema 1.414/STJ",
  "status": "SUSPENSA",
  "desde": "17/03/2026",
  "setor": "FINANCEIRO",
  "porque": "O STJ afetou o Tema 1.414 (06/03/2026) e determinou SUSPENSÃO NACIONAL de todos os processos, individuais e coletivos, que discutam — ainda que em parte — a validade ou abusividade do cartão de crédito consignado (Reserva de Margem Consignável — RMC — e RCC). Vai fixar parâmetros sobre dever de informação, juros rotativos e prazo indeterminado da dívida. Sem prazo definido (expectativa de até ~2 anos).",
  "como_afastar": [
   "AJUIZAR mesmo assim: a suspensão não impede a propositura — protocole para interromper a prescrição e garantir a aplicação futura da tese.",
   "TUTELA DE URGÊNCIA (art. 300 CPC): a suspensão NÃO impede o juiz de analisar liminar para cessar os descontos abusivos — peça a suspensão imediata dos débitos.",
   "DISTINÇÃO (distinguishing): se a causa NÃO discute a validade/abusividade do RMC/RCC em si — ex.: FRAUDE / cartão NÃO CONTRATADO, ou vício de consentimento — requeira a distinção e o prosseguimento, pois foge da controvérsia afetada.",
   "Preservar prova (contrato, extratos, ausência de assinatura) para o momento do julgamento."
  ],
  "fonte": "STJ — Tema Repetitivo 1.414 (afetação 06/03/2026; suspensão 17/03/2026)."
 },
 {
  "tese": "Dívida prescrita em plataformas de renegociação",
  "instrumento": "Tema 1.264/STJ",
  "status": "SUSPENSA",
  "setor": "FINANCEIRO",
  "porque": "Abrange as ações que discutem a legalidade da cobrança extrajudicial e da exibição/inscrição de dívidas prescritas em plataformas de renegociação de débitos (ex.: Serasa Limpa Nome). Discute se expor a dívida prescrita para renegociação é ilícito e gera dano moral.",
  "como_afastar": [
   "DISTINÇÃO: se o caso é de NEGATIVAÇÃO/inscrição em cadastro restritivo (SPC/Serasa) — e não a mera exibição para renegociação — pode não estar na controvérsia afetada.",
   "Ajuizar para interromper prescrição e resguardar o direito; pedir tutela se houver negativação ativa.",
   "Separar o pedido: exclusão do apontamento (urgente) × declaração de ilicitude da exibição (aguarda o tema)."
  ],
  "fonte": "STJ — Tema Repetitivo 1.264."
 },
]

def ativos(): return [s for s in SUSPENSOES if s["status"]=="SUSPENSA"]
if __name__=="__main__":
    print(f"{len(ativos())} teses de consumo com suspensão ativa")
