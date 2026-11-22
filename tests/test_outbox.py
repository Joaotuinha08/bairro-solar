"""Outbox: o evento fica guardado se a publicação falhar e é publicado depois (ARCHITECTURE 2.4)."""

from comum import bd, consumidor, eventos
from operacional import abrir_bd, medicoes
from tests.apoio import encerrado, producao


class BrokerInstavel:
    def __init__(self):
        self.em_baixo = True
        self.recebidos = []

    def __call__(self, routing_key, corpo):
        if self.em_baixo:
            raise ConnectionError("broker em baixo")
        self.recebidos.append(routing_key)


def test_evento_fica_na_outbox_se_publicacao_falhar_e_e_publicado_depois():
    conn = abrir_bd()
    pub = BrokerInstavel()
    consumidor.processar(conn, "op.medicoes", eventos.serializar(producao("T01", 0, 3.0)), medicoes.tratar, pub)
    r = consumidor.processar(conn, "op.medicoes", eventos.serializar(encerrado(0)), medicoes.tratar, pub)
    assert r == consumidor.ACK  # o efeito está gravado; o evento derivado não se perde
    assert [x["evento_id"] for x in bd.outbox_pendentes(conn)] == ["saldo:0"]

    pub.em_baixo = False
    assert bd.publicar_outbox(conn, pub) == 1  # por exemplo, no arranque seguinte
    assert pub.recebidos == ["saldo.calculado"]
    assert bd.outbox_pendentes(conn) == []


def test_falha_no_efeito_desfaz_tudo_e_vai_para_erros():
    conn = abrir_bd()

    def efeito_que_falha(c, evento):
        bd.outbox_adicionar(c, evento)
        raise RuntimeError("falha a meio")

    r = consumidor.processar(conn, "op.medicoes", eventos.serializar(encerrado(0)), efeito_que_falha, lambda *_: None)
    assert r == consumidor.ERRO
    assert bd.outbox_pendentes(conn) == []
    assert not bd.ja_processado(conn, "op.medicoes", "periodo:0")


def test_outbox_nao_duplica_mesmo_evento_id():
    conn = abrir_bd()
    env = encerrado(0)
    bd.outbox_adicionar(conn, env)
    bd.outbox_adicionar(conn, env)
    assert len(bd.outbox_pendentes(conn)) == 1
