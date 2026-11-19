#### ADR-03 - RabbitMQ com uma exchange topic e uma fila por consumidor

- Contexto: o enunciado sugere RabbitMQ e "uma exchange do tipo topic e uma fila por consumidor". O F2 exige que aviso e painel recebam o mesmo evento, "cada um com a sua fila".
- Decisão: exchange `bairro` do tipo `topic`; routing key = tipo do evento; uma fila durável por consumidor (2.3); fila `erros` para mensagens que falham.
- Alternativas: uma fila partilhada (os consumidores dividiriam as mensagens em vez de cada um receber todas); exchange `fanout` (todos receberiam tudo, sem filtro por tipo).
- Consequências: (+) cada consumidor recebe só o que subscreve e ao seu ritmo; acrescentar um consumidor é só criar uma fila e um binding. (−) mais filas para declarar e monitorizar.


