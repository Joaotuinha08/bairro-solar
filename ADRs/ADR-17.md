#### ADR-17 - Excedente e anomalias publicados só na mudança de estado

- Contexto: "Início e fim publicados só quando o estado muda." Para as anomalias, um telhado avariado continuaria anómalo em todos os períodos seguintes.
- Decisão: o excedente guarda o estado (`estado_excedente`) e publica só na mudança. A deteção guarda o estado por telhado (`estado_telhados`) e publica `producao.anomala` só na passagem de normal a anómalo.
- Alternativas: publicar em todos os períodos. Rejeitada porque repetiria avisos e gastaria um pedido ao modelo por período.
- Consequências: (+) menos eventos e menos pedidos ao modelo. (−) se a causa mudar enquanto o telhado continua anómalo, não é reclassificado.
