"""python -m operacional

Liga-se ao broker, declara a topologia e consome op.medicoes, op.excedente, op.aviso,
op.painel e op.acoes (prefetch 10, ack manual)."""

import logging

from comum import bd, broker, consumidor
from operacional import abrir_bd, acoes, aviso, excedente, medicoes, painel

EFEITOS = {
    "op.medicoes": medicoes.tratar,
    "op.excedente": excedente.tratar,
    "op.aviso": aviso.tratar,
    "op.painel": painel.tratar,
    "op.acoes": acoes.tratar,
}
PREFETCH = 10


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    conn = abrir_bd(bd.caminho_bd("operacional.db"))
    conexao = broker.ligar()
    canal = conexao.channel()
    broker.declarar_topologia(canal)
    publicar = broker.Publicador(conexao)

    pendentes = bd.publicar_outbox(conn, publicar)  # o que ficou por publicar antes de cair
    if pendentes:
        print(f"[OPERACIONAL] {pendentes} eventos da outbox publicados no arranque", flush=True)

    canal.basic_qos(prefetch_count=PREFETCH)
    for fila, efeito in EFEITOS.items():
        consumidor.registar(canal, fila, conn, efeito, publicar)
    print(f"[OPERACIONAL] a consumir {', '.join(EFEITOS)}", flush=True)
    try:
        canal.start_consuming()
    except KeyboardInterrupt:
        canal.stop_consuming()
    finally:
        conexao.close()
        conn.close()


if __name__ == "__main__":
    main()
