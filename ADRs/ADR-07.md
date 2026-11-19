#### ADR-07 - Medições e fecho do período na mesma fila

- Contexto: para cumprir o ADR-06 o consumidor tem de saber, sem ambiguidade, que valores chegaram antes do fecho.
- Decisão: `consumo.medido`, `producao.medida` e `periodo.encerrado` vão para a mesma fila `op.medicoes`, e o simulador publica num único canal. O RabbitMQ mantém a ordem dentro de uma fila. O cálculo do saldo e a deteção são feitos no mesmo handler, ao receber o fecho. O mesmo raciocínio aplica-se à fila `triagem`.
- Alternativas: filas separadas para medições e fecho. Rejeitada porque a ordem entre filas diferentes não é garantida e um valor a tempo poderia ser tratado como atrasado.
- Consequências: (+) resultado determinístico e testável. (−) o tratamento das medições não pode ser escalado com vários consumidores em paralelo nesta fila (irrelevante à escala do trabalho).
