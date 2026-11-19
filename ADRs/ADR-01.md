#### ADR-01 - Estilo orientado a eventos (EDA)

- Contexto: o enunciado avalia "desenhar e implementar uma arquitetura orientada a eventos". Os valores chegam por gateways instáveis, com atrasos e duplicados, e a triagem com IA não pode pôr em risco o resto.
- Decisão: os componentes comunicam apenas publicando e subscrevendo eventos num broker. Nenhum componente chama outro diretamente.
- Alternativas: pedidos síncronos (REST) entre serviços. Rejeitada porque a latência e a indisponibilidade acumulam-se na cadeia (Aula 8): se a triagem ou o modelo estiverem lentos, o cálculo do saldo ficaria à espera.
- Consequências: (+) desacoplamento no espaço e no tempo, resiliência (C2), novos consumidores sem alterar produtores. (−) consistência eventual, fluxo mais difícil de seguir, necessidade de idempotência.