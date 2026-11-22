"""Fila op.excedente: mantém o estado do excedente e publica só quando muda (ARCHITECTURE 5.6)."""

from comum import bd, eventos
from operacional import PRODUTOR


def tratar(conn, evento: dict) -> None:
    if evento["tipo"] != "saldo.calculado":
        raise ValueError(f"op.excedente não trata eventos do tipo {evento['tipo']!r}")
    d = evento["dados"]
    periodo = d["periodo"]
    estado = conn.execute("SELECT ativo, ultimo_periodo FROM estado_excedente WHERE id = 1").fetchone()
    if periodo <= estado["ultimo_periodo"]:
        return  # saldo antigo ou fora de ordem: ignorado

    ativo = bool(estado["ativo"])
    if d["excedente"] and not ativo:
        _mudanca(conn, evento, "iniciado")
        ativo = True
    elif not d["excedente"] and ativo:
        _mudanca(conn, evento, "terminado")
        ativo = False
    conn.execute(
        "UPDATE estado_excedente SET ativo = ?, ultimo_periodo = ? WHERE id = 1", (int(ativo), periodo)
    )


def _mudanca(conn, evento: dict, acontecimento: str) -> None:
    d = evento["dados"]
    dados = {"periodo": d["periodo"], "saldo_kw": d["saldo_kw"]}
    bd.outbox_adicionar(conn, eventos.criar_envelope(
        f"excedente.{acontecimento}", eventos.id_excedente(d["periodo"], acontecimento),
        dados, PRODUTOR, evento["ocorrido_em"]))
