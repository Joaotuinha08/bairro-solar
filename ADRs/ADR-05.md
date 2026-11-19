#### ADR-05 - Prevenção de perda de dados nos três pontos e outbox

- Contexto: a Aula 8 identifica três pontos de perda: produtor > broker, broker > consumidor, consumidor > base de dados.
- Decisão: filas e mensagens persistentes com publisher confirms; ack manual só depois do commit; outbox para os eventos derivados (2.4).
- Alternativas: publicar o evento derivado logo após o commit, sem outbox. Rejeitada porque, se o serviço cair entre o commit e a publicação, o evento perde-se e o redelivery seria ignorado como duplicado.
- Consequências: (+) nenhum evento derivado se perde. (−) mais uma tabela e um passo de publicação.
