"""Ligação ao RabbitMQ, topologia (ARCHITECTURE 2.3) e publicação com confirms (2.4).

O pika só é importado quando é preciso, para que os testes corram sem ele.
"""

import os
import time

EXCHANGE = "bairro"
DLX = "bairro.dlx"
FILA_ERROS = "erros"

BINDINGS = {
    "op.medicoes": ["consumo.medido", "producao.medida", "periodo.encerrado"],
    "op.excedente": ["saldo.calculado"],
    "op.aviso": ["excedente.*"],
    "op.painel": ["excedente.*"],
    "op.acoes": ["anomalia.classificada"],
    "triagem": ["producao.medida", "relato.recebido", "producao.anomala"],
}

URL_POR_DEFEITO = "amqp://guest:guest@broker:5672/"


def url_broker() -> str:
    return os.environ.get("RABBITMQ_URL", URL_POR_DEFEITO)


def ligar(url: str | None = None, tentativas: int = 30, espera_s: float = 2.0):
    """Liga-se ao broker com retry: até 30 tentativas, 2 s entre cada (5.3)."""
    import pika

    parametros = pika.URLParameters(url or url_broker())
    parametros.heartbeat = 120  # a chamada ao modelo pode demorar até 30 s
    parametros.blocked_connection_timeout = 60
    for tentativa in range(1, tentativas + 1):
        try:
            return pika.BlockingConnection(parametros)
        except pika.exceptions.AMQPConnectionError as exc:
            print(f"[BROKER] tentativa {tentativa}/{tentativas} falhou ({exc!r}); nova tentativa em {espera_s} s", flush=True)
            time.sleep(espera_s)
    raise ConnectionError(f"não foi possível ligar ao RabbitMQ em {url or url_broker()}")


def declarar_topologia(canal) -> None:
    """Exchange topic durável, DLX fanout com fila 'erros' e uma fila durável por consumidor."""
    canal.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
    canal.exchange_declare(exchange=DLX, exchange_type="fanout", durable=True)
    canal.queue_declare(queue=FILA_ERROS, durable=True)
    canal.queue_bind(queue=FILA_ERROS, exchange=DLX)
    for fila, routing_keys in BINDINGS.items():
        canal.queue_declare(queue=fila, durable=True, arguments={"x-dead-letter-exchange": DLX})
        for rk in routing_keys:
            canal.queue_bind(queue=fila, exchange=EXCHANGE, routing_key=rk)


class Publicador:
    """Publica na exchange `bairro` com mensagens persistentes e publisher confirms.
    Chamável como `publicar(routing_key, corpo)`; lança exceção se o broker não confirmar."""

    def __init__(self, conexao_ou_canal, canal_proprio: bool = True):
        self.canal = conexao_ou_canal.channel() if canal_proprio else conexao_ou_canal
        self.canal.confirm_delivery()

    def __call__(self, routing_key: str, corpo: str) -> None:
        import pika

        self.canal.basic_publish(
            exchange=EXCHANGE,
            routing_key=routing_key,
            body=corpo.encode("utf-8"),
            properties=pika.BasicProperties(delivery_mode=2, content_type="application/json"),
            mandatory=True,  # se nenhuma fila a receber, o broker devolve e dá exceção
        )
