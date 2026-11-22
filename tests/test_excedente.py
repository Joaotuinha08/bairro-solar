"""F2: excedente só publica na mudança; aviso e painel (ARCHITECTURE 5.6 e 6.1)."""

import json

from comum import eventos
from operacional import abrir_bd, aviso, excedente, painel
from tests.apoio import ev


def saldo(periodo, saldo_kw):
    return ev("saldo.calculado", eventos.id_saldo(periodo),
              {"periodo": periodo, "producao_total_kw": 0, "consumo_total_kw": 0, "saldo_kw": saldo_kw,
               "excedente": saldo_kw > 0, "n_telhados": 0, "n_casas": 0}, periodo=periodo)


def mudancas(conn):
    return [(r["routing_key"], json.loads(r["corpo"])["evento_id"])
            for r in conn.execute("SELECT routing_key, corpo FROM outbox ORDER BY rowid")]


def test_dois_saldos_positivos_seguidos_geram_um_unico_inicio():
    conn = abrir_bd()
    for p, s in [(0, -1.0), (1, 2.0), (2, 3.0), (3, -0.5), (4, -1.0)]:
        excedente.tratar(conn, saldo(p, s))
    assert mudancas(conn) == [
        ("excedente.iniciado", "excedente:1:iniciado"),
        ("excedente.terminado", "excedente:3:terminado"),
    ]


def test_saldo_antigo_e_ignorado():
    conn = abrir_bd()
    excedente.tratar(conn, saldo(5, 2.0))
    excedente.tratar(conn, saldo(4, -2.0))  # fora de ordem
    assert mudancas(conn) == [("excedente.iniciado", "excedente:5:iniciado")]


def test_mensagens_de_aviso():
    ini = ev("excedente.iniciado", "excedente:5:iniciado", {"periodo": 5, "saldo_kw": 6.0})
    fim = ev("excedente.terminado", "excedente:9:terminado", {"periodo": 9, "saldo_kw": -2.1})
    assert aviso.mensagem(ini) == "[AVISO] Excedente iniciado no periodo 5 (saldo +6.0 kW). Aproveite a energia!"
    assert aviso.mensagem(fim) == "[AVISO] Excedente terminado no periodo 9 (saldo -2.1 kW)."


def test_painel_guarda_e_mostra_historico(capsys):
    conn = abrir_bd()
    painel.tratar(conn, ev("excedente.iniciado", "excedente:5:iniciado", {"periodo": 5, "saldo_kw": 6.0}))
    painel.tratar(conn, ev("excedente.terminado", "excedente:9:terminado", {"periodo": 9, "saldo_kw": -2.1}))
    saida = capsys.readouterr().out.strip().splitlines()
    assert saida[-1] == "[PAINEL] periodo 5: excedente INICIADO (+6.0 kW) | periodo 9: excedente TERMINADO (-2.1 kW)"
    assert conn.execute("SELECT COUNT(*) FROM painel").fetchone()[0] == 2
