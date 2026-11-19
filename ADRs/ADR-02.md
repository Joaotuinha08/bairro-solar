#### ADR-02 - Topologia broker, não mediator

- Contexto: é preciso escolher entre coreografia (broker) e orquestração (mediator) (Aula 8).
- Decisão: topologia broker. Cada componente reage aos eventos que lhe interessam e anuncia o que fez com um novo evento.
- Alternativas: mediator central que dá comandos a cada serviço. Rejeitado porque o fluxo é curto (fecho > saldo > excedente; anomalia > causa > ação), os períodos são independentes e o F2 exige dois consumidores independentes do mesmo evento, que é exatamente publish/subscribe. Um mediator seria um ponto único de falha e de acoplamento.
- Consequências: (+) desempenho, escalabilidade, desacoplamento. (−) nenhum componente conhece o estado do fluxo completo e a recuperação de erros a meio é difícil. Aceitável porque não há fluxos longos. Passaríamos a mediator se surgisse um processo longo com passos dependentes e compensação (ex.: gestão completa do pedido de intervenção com técnicos externos).