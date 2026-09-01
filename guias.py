#!/usr/bin/env python3
"""
GUIAS práticos por tese emergente — conteúdo jurídico curado (explicação, documentos, como ajuizar).
Chaveado pelo mesmo rótulo `tese` usado em tendencias.py (CAND). Usado pelo dashboard.
Redação própria (não copia terceiros). Precedente de 1º grau/Turma é persuasivo, não vinculante.
"""
GUIAS = {
 "Golpe do PIX": {
  "explicacao": "Vítima é induzida por terceiro (falsa central, link ou perfil clonado) a fazer um PIX ou aprovar transação. Discute-se a responsabilidade do banco pela falha de segurança e pelo monitoramento de transações atípicas. A jurisprudência distingue o 'golpe com falha do banco' (fraude no sistema, conta-fantasma, ausência de alerta) — em regra indenizável — do PIX feito voluntariamente pela própria vítima enganada, onde o êxito é menor e depende de provar falha do serviço.",
  "documentos": ["Extrato/comprovante do PIX contestado","Boletim de Ocorrência","Print das conversas/ligações do golpista","Reclamação registrada no banco (protocolo)","Reclamação no BACEN/consumidor.gov (se houver)","Documento de identidade e comprovante de conta"],
  "como_ajuizar": "Ação declaratória de inexistência de débito c/c indenização por danos materiais (devolução do valor) e morais, com pedido de tutela de urgência para bloqueio/devolução via MED (Mecanismo Especial de Devolução do BACEN). Fundamentar na falha do serviço (art. 14 CDC) e no dever de segurança; requerer inversão do ônus da prova. Juntar o protocolo do MED — pedir a devolução ao banco em até 80 dias é requisito prático importante.",
  "fundamentos": ["CDC art. 14 (responsabilidade objetiva/fortuito interno)","Súmula 479 STJ (fortuito interno das instituições financeiras)","Resolução BCB 103/2021 (MED)","art. 927, § único, CC"],
  "valor_referencia": "Dano material = valor transferido; dano moral quando há falha do banco, tipicamente R$ 3.000–10.000."
 },
 "Engenharia social / falsa central": {
  "explicacao": "Fraudador se passa por central do banco e, por telefone/aplicativo, conduz a vítima a instalar app de acesso remoto, informar senha/token ou aprovar operações. O eixo é a falha de segurança do banco em barrar operações atípicas (empréstimos instantâneos, transferências fora do padrão do cliente). Tese com forte índice de êxito quando há operações destoantes do perfil.",
  "documentos": ["Extratos mostrando as operações atípicas","B.O.","Registro/gravação ou print do contato do golpista","Protocolos de contestação junto ao banco","Histórico de movimentação anterior (para provar o perfil)"],
  "como_ajuizar": "Ação de inexistência de débito (empréstimos/transferências fraudulentas) c/c danos morais e materiais, com tutela para suspender descontos/parcelas. Central: as operações fogem do perfil do consumidor e o banco falhou no monitoramento. Requerer que o banco exiba os logs e a análise antifraude (inversão do ônus).",
  "fundamentos": ["CDC art. 14 e art. 6º, VIII (inversão)","Súmula 479 STJ","Dever de segurança bancária (Res. CMN 4.893/2021)"],
  "valor_referencia": "Anulação dos contratos fraudulentos + dano moral R$ 4.000–12.000 conforme o transtorno e negativação."
 },
 "Biometria facial (fraude)": {
  "explicacao": "Contratação de crédito/conta aprovada por biometria facial que o banco alega ser prova de autoria, mas que foi burlada (foto, deepfake, ou biometria de terceiro). Discute-se se a biometria, isoladamente, comprova que foi o titular quem contratou. Tendência recente por causa da digitalização das contratações.",
  "documentos": ["Contrato/registro que o banco atribui ao cliente","B.O.","Prova de que o cliente não reconhece a operação","Solicitação administrativa da imagem biométrica usada (o banco costuma não exibir)"],
  "como_ajuizar": "Ação declaratória de inexistência do contrato c/c danos morais, exigindo que o banco comprove a autoria (exibição da captura biométrica e do laudo de vivacidade). A ausência dessa prova pesa a favor do consumidor. Tutela para retirar negativação/suspender descontos.",
  "fundamentos": ["CDC art. 14","Súmula 479 STJ","ônus da prova da contratação é do fornecedor (art. 373, II, CPC + art. 6º, VIII, CDC)"],
  "valor_referencia": "Dano moral R$ 4.000–10.000; maior se houve negativação indevida."
 },
 "Conta digital": {
  "explicacao": "Abertura fraudulenta de conta digital em nome da vítima (usada para receber golpes) ou bloqueio/encerramento unilateral de conta legítima. No primeiro caso, dano por uso indevido do CPF; no segundo, discute-se o bloqueio sem justificativa e a retenção de saldo.",
  "documentos": ["Comprovante da conta/bloqueio","B.O. (conta aberta por terceiro)","Notificações do banco","Comprovante de saldo retido"],
  "como_ajuizar": "Conforme o caso: (a) inexistência de relação jurídica c/c danos morais pela conta-fantasma; ou (b) obrigação de fazer para desbloqueio/liberação de saldo c/c danos morais. Tutela de urgência para liberar valores ou remover apontamentos.",
  "fundamentos": ["CDC art. 14","Súmula 479 STJ","boa-fé objetiva (art. 422 CC)"],
  "valor_referencia": "Dano moral R$ 3.000–8.000; liberação integral do saldo retido."
 },
 "Descontos de associação/entidade": {
  "explicacao": "Descontos mensais em benefício do INSS ou em conta, por 'mensalidade associativa' de entidade/sindicato que o segurado nunca autorizou. Fenômeno em forte expansão. Discute-se a ausência de filiação válida e a devolução em dobro dos valores descontados.",
  "documentos": ["Extrato do benefício/conta com os descontos","Histórico de descontos (INSS/Meu INSS)","Ausência de ficha de filiação assinada","Reclamação administrativa (se houver)"],
  "como_ajuizar": "Ação declaratória de inexistência de filiação c/c cessação dos descontos, restituição em dobro e danos morais, contra a associação (e o banco/INSS quando cabível). Tutela para cessar os descontos imediatamente. Cobrar da entidade a prova da autorização expressa.",
  "fundamentos": ["CDC art. 42, § único (repetição em dobro)","art. 6º, VIII, CDC (inversão)","IN INSS sobre autorização de descontos associativos"],
  "valor_referencia": "Restituição em dobro de todos os descontos + dano moral R$ 3.000–8.000."
 },
 "Desconto não autorizado (benefício)": {
  "explicacao": "Empréstimo consignado ou parcela debitada de aposentadoria/pensão sem contratação válida (RMC de cartão consignado, margem usada sem ciência). Diferencia-se do consignado regular: aqui não há contrato assinado ou houve indução a erro.",
  "documentos": ["Extrato de consignações (Meu INSS)","Contrato apontado pelo banco (ou sua ausência)","Comprovante dos descontos","B.O. se houve fraude"],
  "como_ajuizar": "Declaratória de inexistência/nulidade do contrato c/c devolução em dobro e danos morais, com tutela para suspender descontos. Atacar especialmente a Reserva de Margem Consignável (RMC) vendida como empréstimo comum.",
  "fundamentos": ["CDC art. 42, § único","CDC art. 14","Lei 10.820/2003 (consignação)"],
  "valor_referencia": "Suspensão + repetição em dobro; dano moral R$ 3.000–8.000."
 },
 "Superendividamento (Lei 14.181)": {
  "explicacao": "Consumidor de boa-fé com múltiplas dívidas que comprometem o mínimo existencial pode pedir a repactuação global em juízo. Marco recente (Lei 14.181/2021 alterou o CDC), ainda em consolidação nos Juizados.",
  "documentos": ["Relação de todas as dívidas e credores","Comprovantes de renda e despesas essenciais","Extratos e contratos","Comprovante do mínimo existencial comprometido"],
  "como_ajuizar": "Ação de repactuação de dívidas (art. 104-A CDC) requerendo audiência conciliatória global com todos os credores e plano de pagamento que preserve o mínimo existencial. Alternativa administrativa via núcleos de superendividamento/PROCON.",
  "fundamentos": ["CDC arts. 54-A a 54-G e 104-A/104-C (Lei 14.181/2021)","Decreto 11.150/2022 (mínimo existencial)"],
  "valor_referencia": "Não é indenizatória — objetivo é o plano de pagamento; danos morais só em abusos específicos."
 },
 "Rol exemplificativo (Lei 14.454)": {
  "explicacao": "Plano de saúde nega cobertura alegando que o procedimento não está no Rol da ANS. Após a Lei 14.454/2022, o Rol é EXEMPLIFICATIVO: havendo prescrição médica e eficácia comprovada, a cobertura é devida mesmo fora do rol. Marco recente com alto êxito.",
  "documentos": ["Prescrição/relatório médico detalhado","Negativa da operadora por escrito","Contrato do plano","Comprovantes de urgência (se houver)","Evidência científica/eficácia do tratamento"],
  "como_ajuizar": "Obrigação de fazer (autorizar/custear o tratamento) c/c danos morais, com tutela de urgência para cobertura imediata. Fundamentar no caráter exemplificativo do rol e na prescrição médica que se sobrepõe à negativa administrativa.",
  "fundamentos": ["Lei 9.656/98 alterada pela Lei 14.454/2022","CDC art. 51 (cláusula abusiva)","Súmula 102 TJSP (análoga)","dever de cobertura por prescrição médica"],
  "valor_referencia": "Custeio integral do tratamento + dano moral R$ 5.000–15.000 em negativas graves/urgência."
 },
 "Reajuste abusivo (plano de saúde)": {
  "explicacao": "Aumento da mensalidade do plano acima do autorizado — reajuste anual acima do índice da ANS, reajuste por faixa etária desproporcional, ou reajuste por sinistralidade em plano coletivo sem memória de cálculo. Discute-se a abusividade do percentual e a falta de transparência. Em planos individuais, o teto é o da ANS; por faixa etária, veda-se aumento desproporcional (sobretudo após os 60 anos).",
  "documentos": ["Contrato do plano","Boletos/faturas mostrando o valor antes e depois","Comunicado do reajuste aplicado","Demonstrativo/memória de cálculo (exigir da operadora)","Comprovante de idade (reajuste por faixa etária)"],
  "como_ajuizar": "Ação revisional de cláusula c/c repetição do indébito e danos morais, com tutela de urgência para limitar o reajuste ao índice devido e impedir a suspensão do plano por inadimplência do valor controvertido. Exigir a memória de cálculo da sinistralidade; a ausência de transparência gera a abusividade.",
  "fundamentos": ["Lei 9.656/98","Tema 952 STJ (reajuste por faixa etária: exige previsão contratual e proporcionalidade)","Estatuto do Idoso art. 15, § 3º","CDC art. 51, IV e X","Resoluções ANS de reajuste"],
  "valor_referencia": "Limitação do reajuste + restituição do excesso (em dobro quando abusivo); dano moral R$ 2.000–8.000."
 },
 "Negativa de cirurgia reparadora": {
  "explicacao": "Plano nega cirurgia reparadora alegando finalidade estética — típico na cirurgia pós-bariátrica (retirada de excesso de pele), reconstrução de mama pós-mastectomia, ou correção funcional. A jurisprudência entende que a cirurgia reparadora é continuação do tratamento e tem cobertura obrigatória, não sendo estética.",
  "documentos": ["Relatório/prescrição do médico assistente indicando a finalidade reparadora","Negativa da operadora por escrito","Laudos e exames","Histórico do tratamento (ex: cirurgia bariátrica prévia)","Fotos/documentação do quadro clínico"],
  "como_ajuizar": "Obrigação de fazer para autorizar/custear a cirurgia c/c danos morais, com tutela de urgência para realização imediata. Fundamentar que a cirurgia reparadora integra o tratamento e não é estética, prevalecendo a indicação do médico assistente sobre a negativa administrativa.",
  "fundamentos": ["Lei 9.656/98 e Lei 14.454/2022 (rol exemplificativo)","Súmula 97 TJSP e precedentes STJ (reparadora pós-bariátrica é obrigatória)","CDC art. 51","prevalência da prescrição do médico assistente"],
  "valor_referencia": "Custeio integral da cirurgia + dano moral R$ 5.000–15.000 (maior em negativa com urgência/sofrimento)."
 },
 "Bloqueio de conta WhatsApp/Meta": {
  "explicacao": "A Meta (WhatsApp/Facebook/Instagram) bane ou bloqueia a conta do usuário — muito comum no WhatsApp Business usado comercialmente por MEIs e pequenos negócios — em regra sem aviso prévio, sem motivação clara e sem contraditório, alegando violação genérica dos termos de uso. O titular perde acesso a contatos, histórico e clientes, com impacto direto no faturamento. Tese NOVA, em forte expansão (praticamente inexistia em 2024). Discute-se a falha na prestação do serviço, a ausência de motivação/devido processo e os danos materiais (faturamento perdido) e morais.",
  "documentos": ["Print do bloqueio/banimento e das mensagens da Meta","Comprovante de uso comercial da conta (WhatsApp Business, catálogo)","Notas fiscais/faturamento antes do bloqueio (dano material)","Tentativas de recuperação e protocolos de suporte","Cadastro/número vinculado à conta","Contrato social ou CNPJ do MEI (se PJ)"],
  "como_ajuizar": "Ação de obrigação de fazer (reativar/desbloquear a conta) c/c danos materiais e morais, contra META PLATAFORMAS BRASIL LTDA, com pedido de TUTELA DE URGÊNCIA para restabelecimento imediato — o perigo de dano é a perda contínua de clientes. Fundamentar na relação de consumo, na falha do serviço e na ausência de motivação/contraditório do bloqueio. Comprovar o dano material com o faturamento anterior.",
  "fundamentos": ["CDC art. 14 (falha do serviço, responsabilidade objetiva)","CDC art. 6º, VIII (inversão do ônus)","Marco Civil da Internet (Lei 12.965/2014, arts. 7º e 10)","boa-fé objetiva e dever de motivação","Súmula 227 STJ (dano moral à pessoa jurídica)"],
  "valor_referencia": "Reativação da conta + dano material (faturamento comprovadamente perdido) + dano moral R$ 3.000–15.000 (cabível também à PJ)."
 },
 "Casa de apostas / bet": {
  "explicacao": "Conflitos com plataformas de apostas (bets): bloqueio de saldo/saque, não pagamento de prêmio, conta encerrada com retenção de valores, ou uso indevido de dados/PIX. Tema NOVO, explodindo com a regulamentação (Lei 14.790/2023). Discute-se a relação de consumo e o dever de pagar/devolver.",
  "documentos": ["Print do saldo/aposta/prêmio","Histórico de depósitos (PIX/extrato)","Termos da plataforma","Reclamações e protocolos","Comprovante de identidade usado no cadastro"],
  "como_ajuizar": "Ação de obrigação de fazer (liberar saque/pagar prêmio) ou de restituição dos depósitos c/c danos morais, com tutela de urgência. Enfrentar a alegação de 'multiconta'/irregularidade exigindo prova da plataforma. Atenção à legitimidade de bets estrangeiras e à regularização pela Lei 14.790/2023.",
  "fundamentos": ["CDC arts. 14 e 51","Lei 14.790/2023 (apostas de quota fixa)","boa-fé objetiva; vedação ao enriquecimento sem causa"],
  "valor_referencia": "Liberação do saldo/prêmio; dano moral variável (R$ 2.000–8.000) conforme retenção e tempo."
 },
 "Aposta online / bet (bloqueio)": {
  "explicacao": "Subtipo do tema bets: foco no bloqueio de saldo ou recusa de saque sob alegação de verificação (KYC) ou suspeita de fraude, com retenção prolongada de valores do apostador.",
  "documentos": ["Print do bloqueio/recusa","Documentos de verificação já enviados","Histórico de saque/depósito","Protocolos de atendimento"],
  "como_ajuizar": "Obrigação de fazer para liberar o saldo/saque c/c danos morais, tutela de urgência. Exigir que a plataforma aponte a irregularidade concreta; retenção genérica e indefinida é abusiva.",
  "fundamentos": ["CDC art. 14 e 51, IV","Lei 14.790/2023","vedação ao enriquecimento sem causa (art. 884 CC)"],
  "valor_referencia": "Liberação integral; dano moral R$ 2.000–6.000."
 },
 "WhatsApp clonado": {
  "explicacao": "Golpista clona/assume o WhatsApp e pede dinheiro a contatos, ou usa o número para fraudes bancárias. Contra a operadora/banco discute-se falha de segurança (SIM swap, portabilidade fraudulenta) e transações daí decorrentes.",
  "documentos": ["B.O.","Prints das conversas fraudulentas","Registro na operadora (portabilidade/chip)","Extratos das transações fraudulentas"],
  "como_ajuizar": "Contra a operadora: indenização por falha de segurança na portabilidade/SIM swap. Contra o banco: inexistência das operações fraudulentas. Tutela para restabelecer a linha e suspender débitos.",
  "fundamentos": ["CDC art. 14","Súmula 479 STJ (banco)","dever de segurança das telecom (Anatel)"],
  "valor_referencia": "Dano moral R$ 3.000–10.000; devolução dos valores."
 },
 "Falso funcionário do banco": {
  "explicacao": "Fraudador se apresenta como gerente/funcionário e obtém dados, senhas ou aprovação de operações. Muito próximo da engenharia social; alto crescimento. Eixo: falha do banco em monitorar e a inexistência de contratação legítima.",
  "documentos": ["Extratos das operações contestadas","B.O.","Registro/print do contato do falso funcionário","Protocolos de contestação"],
  "como_ajuizar": "Inexistência de débito das operações fraudulentas c/c danos morais e materiais, tutela para suspender parcelas/negativação. Explorar a atipicidade das operações frente ao perfil do cliente.",
  "fundamentos": ["CDC art. 14","Súmula 479 STJ","art. 6º, VIII, CDC"],
  "valor_referencia": "Anulação das operações + dano moral R$ 4.000–12.000."
 },
 "Site/loja falsa": {
  "explicacao": "Consumidor compra em site/loja virtual falsa (ou clonada) e não recebe o produto nem o estorno. Discute-se a responsabilidade da plataforma de pagamento/marketplace e do banco pelo chargeback.",
  "documentos": ["Comprovante da compra e do pagamento","Anúncio/site (prints, URL)","B.O.","Tentativas de contato e protocolos","Pedido de estorno/chargeback"],
  "como_ajuizar": "Restituição do valor c/c danos morais contra o vendedor e, quando cabível, o marketplace/intermediador de pagamento (responsabilidade solidária). Tutela para estorno. Pleitear chargeback junto à administradora do cartão.",
  "fundamentos": ["CDC arts. 14, 18 e 25, § 1º (solidariedade)","Marco Civil da Internet (provedores)","boa-fé objetiva"],
  "valor_referencia": "Devolução integral + dano moral R$ 1.500–6.000."
 },
 "Energia solar (fotovoltaica)": {
  "explicacao": "Contratos de instalação de energia solar com vício (sistema não gera o prometido, instalação defeituosa, financiamento casado). Tema em ascensão com a popularização fotovoltaica.",
  "documentos": ["Contrato de compra/instalação","Proposta com a geração prometida","Faturas de energia antes/depois","Laudos/fotos do defeito","Contrato de financiamento (se houver)"],
  "como_ajuizar": "Ação por vício do produto/serviço (art. 18/20 CDC): reexecução, abatimento ou rescisão c/c devolução e danos morais. Se houve financiamento casado, pedir a rescisão do contrato coligado. Tutela conforme urgência.",
  "fundamentos": ["CDC arts. 18, 20 e 51","contratos coligados (financiamento)","publicidade vinculante (art. 30 CDC)"],
  "valor_referencia": "Abatimento/rescisão + danos; moral R$ 2.000–8.000 conforme o prejuízo."
 },
 "Assinatura recorrente / clube": {
  "explicacao": "Cobrança recorrente de assinatura/clube que o consumidor não contratou, não consegue cancelar, ou continua sendo cobrada após o cancelamento. Inclui 'pegadinhas' de trial que vira cobrança automática.",
  "documentos": ["Faturas com as cobranças recorrentes","Pedido de cancelamento e protocolo","Termos da assinatura","Prints do fluxo de contratação/trial"],
  "como_ajuizar": "Declaratória de inexistência/cessação das cobranças c/c restituição em dobro e danos morais. Atacar a dificuldade de cancelamento (deve ser tão fácil quanto contratar) e a cobrança pós-cancelamento.",
  "fundamentos": ["CDC art. 42, § único","CDC art. 51","Decreto 11.034/2022 (SAC — cancelamento facilitado)"],
  "valor_referencia": "Cessação + repetição em dobro; dano moral R$ 1.000–5.000."
 },
}

def guia(tese): return GUIAS.get(tese)
if __name__=="__main__":
    print(f"{len(GUIAS)} guias curados")
