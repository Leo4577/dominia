#!/usr/bin/env python3
"""
RECEITA DE ÊXITO por tese: passo a passo numerado + prova decisiva + o que faz PERDER + faixa de êxito.
Os passos são gerados a partir dos campos do guia (documentos/como_ajuizar/fundamentos) + boas práticas CDC;
prova decisiva, derrota e faixa de êxito são curados por tese (fallback por setor).
Usado pelo dashboard (modal da tese, aba Tendências). export: receita_de(tese, guia, setor)
"""

# prova decisiva · o que faz perder · faixa de êxito (curado por tese)
CURADO = {
 "Golpe do PIX": ("Provar FALHA do banco: transação atípica sem alerta/bloqueio, conta-destino 'laranja' recém-aberta, ausência de dupla checagem.",
   "PIX feito voluntariamente pela própria vítima, sem demonstrar falha do serviço — vira 'culpa exclusiva de terceiro/vítima'.",
   "Médio — sobe muito quando há falha comprovada do banco; cai no PIX voluntário puro."),
 "Engenharia social / falsa central": ("Registros do banco mostrando operações fora do padrão do cliente e ausência de mecanismo antifraude (Súmula 479 STJ — risco do empreendimento).",
   "Não juntar B.O. nem o histórico de transações; alegar só 'fui enganado' sem apontar a falha do sistema.",
   "Alto — engenharia social com falha do banco tem forte tendência de procedência."),
 "Biometria facial (fraude)": ("Laudo/print de que a biometria não confere ou foi burlada e que o banco não fez verificação adicional.",
   "Deixar de impugnar o contrato/assinatura e não pedir perícia quando a instituição junta 'prova' da contratação.",
   "Alto quando se demonstra a fraude na contratação."),
 "Descontos de associação/entidade": ("Extrato com o desconto + ausência de filiação assinada; a ré não junta autorização expressa e específica.",
   "Existir autorização/filiação válida assinada pelo consumidor.",
   "Muito alto — sem autorização expressa, desconto é indevido (devolução em dobro + dano moral)."),
 "Desconto não autorizado (benefício)": ("Extrato do INSS/benefício com o débito e a não contratação; inversão do ônus para a ré provar a contratação.",
   "A ré comprovar contrato/áudio de contratação válido.",
   "Alto — descontos em benefício sem prova de contratação costumam ser afastados."),
 "Reajuste abusivo (plano de saúde)": ("Demonstrativo do reajuste acima do índice/ANS ou por faixa etária sem base atuarial (Tema 952 STJ, Estatuto do Idoso).",
   "Reajuste dentro do índice autorizado e com previsão contratual clara e atuarialmente justificada.",
   "Médio-alto — reajuste por faixa etária abusivo e reajustes sem transparência tendem a cair."),
 "Negativa de cirurgia reparadora": ("Relatório médico indicando a finalidade FUNCIONAL (não estética) + rol exemplificativo (Lei 14.454/2022).",
   "Ausência de indicação médica ou procedimento meramente estético sem repercussão funcional.",
   "Alto — com laudo funcional, a negativa costuma ser abusiva."),
 "Rol exemplificativo (Lei 14.454)": ("Prescrição médica do tratamento + comprovação de eficácia/necessidade; a natureza exemplificativa do rol (Lei 14.454/2022).",
   "Tratamento experimental sem comprovação científica ou sem prescrição do médico assistente.",
   "Médio-alto — depende da prova de necessidade e eficácia."),
 "Superendividamento (Lei 14.181)": ("Planilha de comprometimento de renda acima do mínimo existencial + boa-fé do consumidor (Lei 14.181/2021).",
   "Dívidas de luxo/má-fé ou renda não comprometida além do mínimo existencial.",
   "Emergente — repactuação vem sendo deferida quando comprovado o comprometimento excessivo."),
 "Bloqueio de conta WhatsApp/Meta": ("Provar a titularidade/uso legítimo, tentativa de recuperação e a ausência de canal efetivo de suporte da plataforma.",
   "Bloqueio por violação real de termos (spam, fraude) comprovada pela plataforma.",
   "Emergente — tutela para restabelecer a conta vem sendo concedida; dano moral varia."),
 "Casa de apostas / bet": ("Extrato dos depósitos/saques negados + termos da plataforma; falha na prestação do serviço (saque não liberado).",
   "Descumprimento de regra legítima de KYC/limite pelo próprio apostador.",
   "Emergente — foco em saque retido e publicidade enganosa."),
 "Aposta online / bet (bloqueio)": ("Comprovação do saldo e do saque negado sem justificativa idônea.",
   "Bloqueio por suspeita de fraude documentada ou autoexclusão.",
   "Emergente — tendência de restituição do saldo comprovado."),
 "WhatsApp clonado": ("Prova de que o golpe partiu de falha de segurança da instituição pagadora e transação atípica sem alerta.",
   "Transferência feita pela própria vítima ao golpista sem falha do banco.",
   "Médio — depende de imputar falha ao banco/serviço."),
 "Falso funcionário do banco": ("Registros de que o banco não bloqueou operação claramente atípica (Súmula 479 STJ).",
   "Vítima que fornece senha/token voluntariamente sem falha demonstrável do banco.",
   "Médio-alto quando há falha do dever de segurança."),
 "Site/loja falsa": ("Comprovante de pagamento + não entrega + meio de pagamento/intermediador que falhou no dever de cautela.",
   "Compra fora de plataforma que dê rastreabilidade, sem qualquer intermediário responsável.",
   "Médio — cresce contra marketplaces/intermediadores de pagamento."),
 "Energia solar (fotovoltaica)": ("Contrato + laudo de vício/subdimensionamento ou não instalação; descumprimento do prometido.",
   "Sistema entregue conforme contratado e funcionando dentro do prometido.",
   "Médio — vício do produto/serviço e propaganda enganosa."),
 "Assinatura recorrente / clube": ("Print da ausência de contratação/consentimento claro + dificuldade de cancelamento (dark pattern).",
   "Consentimento válido e cancelamento disponibilizado de forma simples.",
   "Alto — cobrança sem consentimento claro é indevida."),
 "Conta digital": ("Prova do bloqueio/encerramento unilateral sem aviso e do prejuízo (contas, salário).",
   "Encerramento com aviso prévio e justa causa contratual comprovada.",
   "Médio — foco em bloqueio abusivo e retenção de saldo."),
}
SETOR_FALLBACK = {
 "FINANCEIRO": ("Extrato do débito/operação contestada + inversão do ônus (art. 6º, VIII, CDC) para a ré provar a contratação.",
   "A instituição comprovar contratação/autorização válida.",
   "Médio-alto — ver o % ao vivo na Consulta."),
 "SAUDE": ("Relatório/prescrição do médico assistente demonstrando necessidade + rol exemplificativo (Lei 14.454/2022).",
   "Falta de indicação médica ou exclusão contratual legítima.",
   "Médio-alto — ver o % ao vivo na Consulta."),
 "CONSUMO": ("Comprovante da falha + reclamação administrativa com protocolo; inversão do ônus da prova.",
   "Não comprovar a falha do fornecedor ou o dano.",
   "Ver o % ao vivo na Consulta."),
}

def _passos(guia, prova):
    docs=guia.get("documentos") or []
    fund=guia.get("fundamentos") or []
    como=guia.get("como_ajuizar") or ""
    valref=guia.get("valor_referencia") or ""
    p=[]
    p.append("Esgote a via administrativa: registre reclamação com protocolo (e, se cabível, BACEN/consumidor.gov). A recusa documentada reforça o dano moral.")
    if docs:
        p.append("Reúna as provas essenciais: "+"; ".join(docs[:6])+".")
    if prova:
        p.append("Garanta a PROVA DECISIVA do seu caso: "+prova)
    if como:
        p.append("Ajuíze a ação correta: "+como.rstrip(".")+".")
    p.append("Peça a inversão do ônus da prova (art. 6º, VIII, CDC): a relação é de consumo e a fornecedora detém os registros.")
    p.append("Requeira tutela de urgência quando houver negativação, negativa de cobertura, bloqueio ou desconto em curso (art. 300, CPC).")
    if fund:
        p.append("Fundamente com: "+", ".join(fund[:6])+".")
    p.append("Dano moral: sustente in re ipsa quando cabível"+(f" e peça {valref}" if valref else "")+"; peça a devolução em dobro (art. 42, § único, CDC) quando houver cobrança indevida.")
    return p

def receita_de(tese, guia, setor):
    prova, derrota, exito = CURADO.get(tese) or SETOR_FALLBACK.get(setor) or SETOR_FALLBACK["CONSUMO"]
    return {"passos": _passos(guia or {}, prova),
            "prova_decisiva": prova, "o_que_faz_perder": derrota, "faixa_exito": exito}

if __name__=="__main__":
    import guias, json
    for t in ["Negativa de cirurgia reparadora","Golpe do PIX","Descontos de associação/entidade"]:
        r=receita_de(t, guias.GUIAS.get(t,{}), "CONSUMO")
        print("\n===",t,"— êxito:",r["faixa_exito"])
        for i,s in enumerate(r["passos"],1): print(f"  {i}. {s}")
        print("  PROVA DECISIVA:",r["prova_decisiva"])
        print("  PERDE SE:",r["o_que_faz_perder"])
