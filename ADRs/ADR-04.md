#### ADR-04 - Entrega pelo menos uma vez e consumidores idempotentes

- Contexto: o gateway reenvia valores "por vezes em duplicado" e o RabbitMQ volta a entregar mensagens sem ack. O F1 exige que "duplicados não contam duas vezes".
- Decisão: aceitar entregas repetidas e tornar todos os consumidores idempotentes com `evento_id` determinístico e a tabela `eventos_processados` (2.5). As medições têm também `UNIQUE(tipo, origem_id, periodo)`.
- Alternativas: entrega "no máximo uma vez" (ack automático), rejeitada porque perde mensagens; "exatamente uma vez" no broker, rejeitada porque o RabbitMQ não a garante.
- Consequências: (+) nenhum valor se perde e nenhum conta duas vezes (C1). (−) cada consumidor precisa de uma tabela e de uma verificação extra.
