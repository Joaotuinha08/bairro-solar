"""F1: idempotência, valores atrasados e saldo (ARCHITECTURE 6.1)."""

import json

from comum import consumidor, eventos
from operacional import abrir_bd, medicoes
from tests.apoio import consumo, encerrado, producao

FILA = "op.medicoes"


def entregar(conn, envelope, publicados=None):
    publicados = publicados if publicados is not None else []
    return consumidor.processar(conn, FILA, eventos.serializar(envelope), medicoes.tratar,
                                lambda rk, corpo: publicados.append((rk, json.loads(corpo))))


def saldo(conn, periodo):
    return conn.execute("SELECT * FROM saldos WHERE periodo = ?", (periodo,)).fetchone()


def test_mesma_producao_entregue_duas_vezes_conta_uma_vez():
    """Reenvio do gateway e nova entrega do RabbitMQ: o mesmo evento_id chega duas vezes."""
    conn = abrir_bd()
    m = producao("T01", 0, 3.0)
    assert entregar(conn, m) == consumidor.ACK
    assert entregar(conn, m) == consumidor.DUPLICADO
    entregar(conn, consumo("C01", 0, 1.0))
    entregar(conn, encerrado(0))
    s = saldo(conn, 0)
    assert s["producao_total_kw"] == 3.0
    assert s["n_telhados"] == 1
    assert conn.execute("SELECT COUNT(*) FROM medicoes").fetchone()[0] == 2


def test_unique_protege_mesma_origem_e_periodo_mesmo_sem_eventos_processados():
    """Segunda proteção: UNIQUE(tipo, origem_id, periodo), mesmo que o handler corra duas vezes."""
    conn = abrir_bd()
    m = producao("T01", 0, 3.0)
    medicoes.tratar(conn, m)
    medicoes.tratar(conn, m)
    entregar(conn, encerrado(0))
    assert saldo(conn, 0)["producao_total_kw"] == 3.0


def test_valor_atrasado_guardado_sem_alterar_saldo_publicado():
    conn = abrir_bd()
    publicados = []
    entregar(conn, producao("T01", 0, 3.0), publicados)
    entregar(conn, encerrado(0), publicados)
    antes = dict(saldo(conn, 0))
    entregar(conn, producao("T02", 0, 2.0), publicados)  # chega depois do fecho
    entregar(conn, consumo("C01", 0, 1.0), publicados)
    assert dict(saldo(conn, 0)) == antes
    atrasados = conn.execute("SELECT origem_id FROM medicoes WHERE atrasado = 1 ORDER BY origem_id").fetchall()
    assert [r[0] for r in atrasados] == ["C01", "T02"]
    saldos_publicados = [e for rk, e in publicados if rk == "saldo.calculado"]
    assert len(saldos_publicados) == 1 and saldos_publicados[0]["dados"]["saldo_kw"] == 3.0


def test_saldo_soma_e_excedente_so_quando_positivo():
    conn = abrir_bd()
    publicados = []
    for t, kw in [("T01", 2.0), ("T02", 1.5)]:
        entregar(conn, producao(t, 0, kw), publicados)
    for c in ["C01", "C02"]:
        entregar(conn, consumo(c, 0, 1.0), publicados)
    entregar(conn, encerrado(0), publicados)
    # período 1: saldo exatamente 0 -> sem excedente
    entregar(conn, producao("T01", 1, 2.0), publicados)
    entregar(conn, consumo("C01", 1, 2.0), publicados)
    entregar(conn, encerrado(1), publicados)

    s0, s1 = saldo(conn, 0), saldo(conn, 1)
    assert (s0["producao_total_kw"], s0["consumo_total_kw"], s0["saldo_kw"]) == (3.5, 2.0, 1.5)
    assert s0["excedente"] == 1 and s0["n_telhados"] == 2 and s0["n_casas"] == 2
    assert s1["saldo_kw"] == 0 and s1["excedente"] == 0

    ev = [e for rk, e in publicados if rk == "saldo.calculado"]
    assert ev[0]["evento_id"] == "saldo:0"
    assert ev[0]["dados"] == {"periodo": 0, "producao_total_kw": 3.5, "consumo_total_kw": 2.0,
                              "saldo_kw": 1.5, "excedente": True, "n_telhados": 2, "n_casas": 2}
    assert ev[1]["dados"]["excedente"] is False


def test_periodo_encerrado_repetido_nao_republica():
    conn = abrir_bd()
    publicados = []
    entregar(conn, producao("T01", 0, 3.0), publicados)
    entregar(conn, encerrado(0), publicados)
    assert entregar(conn, encerrado(0), publicados) == consumidor.DUPLICADO
    assert len([1 for rk, _ in publicados if rk == "saldo.calculado"]) == 1


def test_mensagem_ilegivel_vai_para_erros():
    conn = abrir_bd()
    r = consumidor.processar(conn, FILA, b"isto nao e json", medicoes.tratar, lambda *_: None)
    assert r == consumidor.ERRO
