#!/usr/bin/env python3
"""
Configuração das teses do JUZIA — 1 entrada por grupo.
Adicionar uma tese nova = adicionar um bloco aqui. O orquestrador consome isto.
Cada grupo define: frases de busca (COM acento — a API exige), micro-teses (enum) e o prompt do domínio.
"""

def build_schema(micro_teses):
    return {
      "type":"object","additionalProperties":False,
      "properties":{
        "e_merito":{"type":"boolean","description":"É decisão de mérito sobre ESTE tema? false = descartar do cálculo"},
        "micro_tese":{"type":"string","enum":micro_teses},
        "resultado_consumidor":{"type":"string","enum":["GANHOU","PARCIAL","PERDEU","NAO_APLICA"],
            "description":"Procedência final sob a ótica do consumidor/autor"},
        "dano_moral_concedido":{"type":"boolean"},
        "dano_moral_valor_reais":{"type":"number","description":"Valor do dano moral em reais; 0 se não concedido"},
        "dano_material_concedido":{"type":"boolean"},
        "fundamentos":{"type":"array","items":{"type":"string"},"description":"1-4 fundamentos determinantes"},
        "prova_decisiva":{"type":"array","items":{"type":"string"}},
        "comarca":{"type":"string"},"vara_origem":{"type":"string"},
        "confianca":{"type":"string","enum":["ALTA","MEDIA","BAIXA"]}
      },
      "required":["e_merito","micro_tese","resultado_consumidor","dano_moral_concedido",
                  "dano_moral_valor_reais","dano_material_concedido","fundamentos","prova_decisiva","confianca"]
    }

BASE_SYS=("Você é analista de jurimetria de acórdãos das Turmas Recursais dos Juizados Especiais da Bahia. "
          "Baseie-se SOMENTE no texto fornecido; não invente valores nem fundamentos. "
          "'resultado_consumidor' é a procedência final para o AUTOR/consumidor: GANHOU (pedidos acolhidos), "
          "PARCIAL (parte acolhida), PERDEU (improcedência mantida). Campo ausente = vazio/0. ")

GRUPOS = {

  "AEREO": {
    "frases": ['"extravio de bagagem"','"atraso de voo"','"cancelamento de voo"','"overbooking"','"bagagem danificada"'],
    "micro_teses": ["EXTRAVIO_DEFINITIVO","EXTRAVIO_TEMPORARIO","BAGAGEM_DANIFICADA","ATRASO_MAIOR_4H",
                    "ATRASO_MENOR_4H","CANCELAMENTO_VOO","OVERBOOKING","OUTRO"],
    "sys_extra": ("Domínio: transporte aéreo. Atenção: atraso < 4h costuma ser 'mero dissabor' (art. 251-A CBA/Lei 14.034/2020); "
                  "extravio/avaria gera dano moral in re ipsa; Súmula 04 da Turma de Uniformização TJBA dispensa notas fiscais."),
  },

  "FINANCEIRO": {
    "frases": ['"negativação indevida"','"empréstimo não contratado"','"empréstimo consignado"','"desconto indevido"',
               '"transação não reconhecida"','"golpe"','"tarifa"'],
    "micro_teses": ["NEGATIVACAO_INDEVIDA","EMPRESTIMO_NAO_CONTRATADO","EMPRESTIMO_CONSIGNADO_REGULAR",
                    "DESCONTO_INDEVIDO","TRANSACAO_NAO_RECONHECIDA_FRAUDE","GOLPE_ENGENHARIA_SOCIAL",
                    "TARIFA_ABUSIVA","REVISAO_CONTRATUAL_JUROS","OUTRO"],
    "sys_extra": ("Domínio: instituições financeiras/bancos. Atenção: fraude/transação não reconhecida atrai responsabilidade "
                  "do banco (Súmula 479 STJ, fortuito interno); negativação só gera dano moral se NÃO houver negativação "
                  "legítima preexistente (Súmula 385 STJ); consignado regularmente contratado costuma ser improcedente."),
  },

  "COELBA": {
    "frases": ['"Coelba"','"recuperação de consumo"','"termo de ocorrência de irregularidade"','"suspensão do fornecimento"'],
    "micro_teses": ["RECUPERACAO_CONSUMO_TOI","CORTE_DEBITO_ATUAL","CORTE_DEBITO_PRETERITO",
                    "FATURA_EXCESSIVA","OBRIGACAO_FAZER_LIGACAO","OUTRO"],
    "sys_extra": ("Domínio: energia elétrica (Coelba/Neoenergia). Considere só casos da concessionária de energia. Atenção: "
                  "recuperação de consumo por TOI unilateral, sem perícia idônea/contraditório, tende a ser NULA; corte por "
                  "débito pretérito/controverso é ilegal; corte por débito atual com aviso é legítimo."),
  },

  "EMBASA": {
    "frases": ['"Embasa"','"suspensão do fornecimento"','"cobrança por estimativa"'],
    "micro_teses": ["CORTE_AGUA_DEBITO_ATUAL","CORTE_AGUA_DEBITO_PRETERITO","COBRANCA_ESTIMATIVA",
                    "ESGOTO_DANO_REPARACAO","TARIFA_ESGOTO_SEM_COLETA","OUTRO"],
    "sys_extra": ("Domínio: água/saneamento (Embasa). Considere só casos da concessionária de água/esgoto. Atenção: corte por "
                  "débito antigo/pretérito é ilegal; cobrança por estimativa sem leitura de hidrômetro é indevida; "
                  "tarifa de esgoto sem coleta/tratamento é discutível."),
  },

  "SAUDE": {
    "frases": ['"plano de saúde"','"negativa de cobertura"','"reajuste por faixa etária"','"rol da ANS"','"home care"'],
    "micro_teses": ["NEGATIVA_COBERTURA_PROCEDIMENTO","NEGATIVA_MEDICAMENTO","REAJUSTE_FAIXA_ETARIA",
                    "REAJUSTE_ANUAL","ROL_ANS_TAXATIVIDADE","HOME_CARE","OUTRO"],
    "sys_extra": ("Domínio: planos de saúde. Atenção: negativa de procedimento com indicação do médico assistente tende a ser "
                  "abusiva; reajuste por faixa etária tem limites (Tema 952 STJ, Estatuto do Idoso); o rol da ANS é "
                  "EXEMPLIFICATIVO após a Lei 14.454/2022."),
  },
}

def config(grupo):
    g = GRUPOS[grupo]
    return {
      "frases": g["frases"],
      "schema": build_schema(g["micro_teses"]),
      "system": BASE_SYS + g["sys_extra"],
    }
