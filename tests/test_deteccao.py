"""Deteção de anomalias (ARCHITECTURE 3.1 passo 1 e 6.1)."""

from operacional import abrir_bd, medicoes
from tests.apoio import encerrado, producao


def periodo(conn, p, valores, rua="R1"):
    for t, kw in valores.items():
        medicoes.tratar(conn, producao(t, p, kw, rua_id=rua))
    medicoes.tratar(conn, encerrado(p))
    return conn.execute(
        "SELECT corpo FROM outbox WHERE routing_key = 'producao.anomala' AND evento_id LIKE ?",
        (f"anomalia:%:{p}",),
    ).fetchall()


def test_menos_de_3_vizinhos_nao_avalia():
    conn = abrir_bd()
    assert periodo(conn, 0, {"T01": 0.0, "T02": 3.0, "T03": 3.0}) == []


def test_exatamente_40_por_cento_abaixo_e_anomalia():
    conn = abrir_bd()
    anomalias = periodo(conn, 0, {"T01": 1.8, "T02": 3.0, "T03": 3.0, "T04": 3.0})
    assert len(anomalias) == 1
    import json
    d = json.loads(anomalias[0]["corpo"])["dados"]
    assert d == {"anomalia_id": "anomalia:T01:0", "telhado_id": "T01", "rua_id": "R1", "periodo": 0,
                 "producao_kw": 1.8, "media_vizinhos_kw": 3.0, "desvio_pct": 40.0}


def test_pouco_menos_de_40_por_cento_nao_e_anomalia():
    conn = abrir_bd()
    assert periodo(conn, 0, {"T01": 1.81, "T02": 3.0, "T03": 3.0, "T04": 3.0}) == []


def test_rua_inteira_baixa_nao_ha_anomalia():
    conn = abrir_bd()
    periodo(conn, 0, {"T01": 3.0, "T02": 3.0, "T03": 3.0, "T04": 3.0})
    assert periodo(conn, 1, {"T01": 1.0, "T02": 1.0, "T03": 1.0, "T04": 1.0}) == []


def test_noite_media_zero_nao_avalia():
    conn = abrir_bd()
    assert periodo(conn, 0, {"T01": 0.0, "T02": 0.0, "T03": 0.0, "T04": 0.0}) == []


def test_continua_anomalo_nao_repete_e_volta_a_publicar_depois_de_normal():
    conn = abrir_bd()
    baixo = {"T01": 1.0, "T02": 3.0, "T03": 3.0, "T04": 3.0}
    assert len(periodo(conn, 0, baixo)) == 1
    assert periodo(conn, 1, baixo) == []           # continua anómalo
    assert periodo(conn, 2, {t: 3.0 for t in baixo}) == []  # volta ao normal, sem evento
    assert conn.execute("SELECT anomalo FROM estado_telhados WHERE telhado_id='T01'").fetchone()[0] == 0
    assert len(periodo(conn, 3, baixo)) == 1       # nova passagem a anómalo


def test_ruas_diferentes_nao_sao_vizinhas():
    conn = abrir_bd()
    for t in ["T01", "T02", "T03"]:
        medicoes.tratar(conn, producao(t, 0, 3.0, rua_id="R1"))
    medicoes.tratar(conn, producao("T05", 0, 0.5, rua_id="R2"))
    medicoes.tratar(conn, encerrado(0))
    assert conn.execute("SELECT COUNT(*) FROM outbox WHERE routing_key='producao.anomala'").fetchone()[0] == 0


def test_valor_atrasado_nao_entra_na_detecao():
    conn = abrir_bd()
    periodo(conn, 0, {"T02": 3.0, "T03": 3.0, "T04": 3.0})
    medicoes.tratar(conn, producao("T01", 0, 0.0))  # atrasado
    assert conn.execute("SELECT COUNT(*) FROM outbox WHERE routing_key='producao.anomala'").fetchone()[0] == 0
