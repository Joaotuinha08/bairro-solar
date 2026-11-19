#### ADR-12 - Validação da resposta e regra sem IA

- Contexto: "A resposta do modelo é validada [...]. Se for inválida ou não chegar, aplica-se uma regra sem IA, definida pelo grupo; na dúvida, a causa é avaria." F4: "F1 e F2 continuam; F3 usa a regra sem IA."
- Decisão: validação estrita (3.4) e regra determinística baseada nos números e em palavras-chave (3.5), com `avaria` por omissão.
- Alternativas: voltar a perguntar ao modelo (gasta o limite de pedidos e pode falhar de novo); descartar a anomalia (perderia avarias reais).
- Consequências: (+) há sempre uma causa publicada; avaria por omissão é o lado seguro (um técnico verifica). (−) a regra é menos precisa do que o modelo e pode gerar pedidos de intervenção a mais.
