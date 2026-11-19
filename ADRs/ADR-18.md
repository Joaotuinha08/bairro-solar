#### ADR-18 - Python, pika e GitHub Models

- Contexto: o enunciado permite Python, Java ou TypeScript e recomenda GitHub Models.
- Decisão: Python 3.12 com `pika` (RabbitMQ), `sqlite3` (biblioteca padrão), `openai` (cliente compatível com GitHub Models) e `pytest`.
- Alternativas: Java com `amqp-client` ou TypeScript com `amqplib`. Escolheu-se Python por ser a linguagem que o grupo domina melhor e pelo código mais curto.
- Consequências: (+) menos código, arranque rápido. (−) `pika` não é thread-safe: cada processo usa uma ligação e um canal, e consome várias filas nesse canal.
