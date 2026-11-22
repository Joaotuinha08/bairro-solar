"""python -m triagem

Consome a fila `triagem` com prefetch=1: no máximo um pedido ao modelo em curso (3.7)."""

import logging
from functools import partial

from comum import bd, broker, consumidor
from triagem import abrir_bd, servico
from triagem.modelo import criar_modelo

FILA = "triagem"
PREFETCH = 1


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    modelo = criar_modelo()
    conn = abrir_bd(bd.caminho_bd("triagem.db"))
    conexao = broker.ligar()
    canal = conexao.channel()
    broker.declarar_topologia(canal)
    publicar = broker.Publicador(conexao)

    pendentes = bd.publicar_outbox(conn, publicar)
    if pendentes:
        print(f"[TRIAGEM] {pendentes} eventos da outbox publicados no arranque", flush=True)

    canal.basic_qos(prefetch_count=PREFETCH)
    consumidor.registar(canal, FILA, conn, partial(servico.tratar, modelo=modelo), publicar)
    print(f"[TRIAGEM] a consumir '{FILA}' com o modelo {modelo.nome}", flush=True)
    try:
        canal.start_consuming()
    except KeyboardInterrupt:
        canal.stop_consuming()
    finally:
        conexao.close()
        conn.close()


if __name__ == "__main__":
    main()
