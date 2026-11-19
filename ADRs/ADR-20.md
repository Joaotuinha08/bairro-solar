#### ADR-20 - Docker Compose e saídas na consola

- Contexto: "docker compose up mais um comando arrancam tudo. Avisos, painel e pedidos de intervenção são mensagens na consola."
- Decisão: um único `Dockerfile` para todos os serviços; um `docker-compose.yml` com `broker`, `operacional`, `triagem` e `simulador`. Cada serviço liga-se a `broker` (não a `localhost`) e volta a tentar até o RabbitMQ estar pronto. Aviso, painel, ações e triagem escrevem linhas com prefixos fixos na consola.
- Alternativas: instalar tudo à mão (difícil de reproduzir pelo professor).
- Consequências: (+) arranque igual em qualquer máquina. (−) é preciso ter Docker (ou usar o GitHub Codespace).

