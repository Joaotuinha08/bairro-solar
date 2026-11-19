#### ADR-15 - Uma anomalia de cada vez

- Contexto: "Uma anomalia de cada vez, para respeitar o limite de pedidos dos planos gratuitos."
- Decisão: fila `triagem` com `prefetch=1` e uma única chamada ao modelo por anomalia.
- Alternativas: processar várias anomalias em paralelo (excederia o limite de pedidos).
- Consequências: (+) nunca há pedidos simultâneos. (−) com muitas anomalias, a triagem fica mais lenta (as anomalias esperam na fila, sem se perderem).


