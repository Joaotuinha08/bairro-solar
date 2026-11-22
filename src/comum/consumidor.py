"""Handler genérico idempotente usado por todos os consumidores (ARCHITECTURE 5.3).

`processar` não depende do RabbitMQ: recebe o corpo da mensagem, a ligação SQLite, o efeito
do consumidor e a função de publicação, e devolve o que fazer com a mensagem.
`registar` liga `processar` a uma fila real do pika (ack / nack sem reentrega).
"""

import logging
import sqlite3
import traceback

from comum import bd, eventos

log = logging.getLogger(__name__)

ACK = "ack"
DUPLICADO = "duplicado"  # também leva ack
ERRO = "erro"            # nack sem reentrega -> fila erros


def processar(conn: sqlite3.Connection, fila: str, corpo, efeito, publicar) -> str:
    """efeito(conn, evento) executa o efeito do consumidor dentro da transação
    (pode inserir linhas na outbox). publicar(routing_key, corpo) publica com confirms."""
    try:
        evento = eventos.ler_evento(corpo)
    except ValueError as exc:
        print(f"[ERRO] {fila}: mensagem ilegível enviada para 'erros': {exc}", flush=True)
        return ERRO

    try:
        conn.execute("BEGIN IMMEDIATE")
        if bd.ja_processado(conn, fila, evento["evento_id"]):
            conn.execute("ROLLBACK")
            return DUPLICADO
        efeito(conn, evento)
        bd.marcar_processado(conn, fila, evento["evento_id"])
        conn.execute("COMMIT")
    except Exception as exc:  # noqa: BLE001 - qualquer falha vai para a fila erros
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        print(f"[ERRO] {fila}: falha a processar {evento.get('evento_id')}: {exc}", flush=True)
        log.debug(traceback.format_exc())
        return ERRO

    bd.publicar_outbox(conn, publicar)
    return ACK


def registar(canal, fila: str, conn: sqlite3.Connection, efeito, publicar) -> None:
    """Consome `fila` com ack manual."""

    def ao_receber(ch, metodo, _propriedades, corpo):
        resultado = processar(conn, fila, corpo, efeito, publicar)
        if resultado == ERRO:
            ch.basic_nack(delivery_tag=metodo.delivery_tag, requeue=False)
        else:
            ch.basic_ack(delivery_tag=metodo.delivery_tag)

    canal.basic_consume(queue=fila, on_message_callback=ao_receber, auto_ack=False)
