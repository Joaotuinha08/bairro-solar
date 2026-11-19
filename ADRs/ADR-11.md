#### ADR-11 - A IA como um passo de workflow; o código decide a ação

- Contexto: "O código decide a ação; o modelo só escolhe a causa." A Aula 10 recomenda o mínimo de autonomia que satisfaz os requisitos.
- Decisão: o fluxo é fixo em código (deteção > classificação > ação). O modelo faz só a classificação (padrão routing, nível 3 do espectro de autonomia). A ação vem da tabela 3.1.
- Alternativas: um agente com ferramentas que decidisse e executasse a ação. Rejeitado: menos previsível, menos testável, mais caro e com risco de ações erradas.
- Consequências: (+) comportamento previsível e testável; um erro do modelo só pode trocar a causa. (−) casos fora das três causas não são tratados.
