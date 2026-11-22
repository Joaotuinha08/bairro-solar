"""Fila op.painel: guarda e mostra o histórico de mudanças de excedente (ARCHITECTURE 5.6)."""

from comum import bd

TIPOS = {"excedente.iniciado": "iniciado", "excedente.terminado": "terminado"}


def tratar(conn, evento: dict) -> None:
    if evento["tipo"] not in TIPOS:
        raise ValueError(f"op.painel não trata eventos do tipo {evento['tipo']!r}")
    d = evento["dados"]
    conn.execute(
        "INSERT INTO painel (periodo, tipo, saldo_kw, registado_em) VALUES (?, ?, ?, ?)",
        (d["periodo"], TIPOS[evento["tipo"]], d["saldo_kw"], bd.agora()),
    )
    print(historico(conn), flush=True)


def historico(conn) -> str:
    linhas = conn.execute("SELECT periodo, tipo, saldo_kw FROM painel ORDER BY periodo, rowid").fetchall()
    partes = [f"periodo {l['periodo']}: excedente {l['tipo'].upper()} ({l['saldo_kw']:+.1f} kW)" for l in linhas]
    return "[PAINEL] " + " | ".join(partes)
