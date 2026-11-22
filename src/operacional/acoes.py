"""Fila op.acoes: deriva a ação só da causa e escreve a mensagem (ARCHITECTURE 3.1 passo 3).

A justificação do modelo nunca é usada aqui: as mensagens são texto fixo escrito pelo código.
"""

from comum import bd

ACOES = {
    "sombra": "nenhuma",
    "sujidade": "avisar_membro",
    "avaria": "pedido_intervencao",
}


def mensagem(causa: str, telhado_id: str, periodo: int) -> str:
    if causa == "sombra":
        return f"[ACAO] Telhado {telhado_id} (periodo {periodo}): sombra temporaria, nenhuma acao."
    if causa == "sujidade":
        return (f"[MEMBRO M-{telhado_id}] A producao do seu painel esta abaixo da dos vizinhos, "
                f"provavelmente por sujidade. Por favor limpe o painel.")
    if causa == "avaria":
        return f"[INTERVENCAO] Pedido de intervencao registado para o telhado {telhado_id} (periodo {periodo})."
    raise ValueError(f"causa desconhecida: {causa!r}")


def tratar(conn, evento: dict) -> None:
    if evento["tipo"] != "anomalia.classificada":
        raise ValueError(f"op.acoes não trata eventos do tipo {evento['tipo']!r}")
    d = evento["dados"]
    causa = d["causa"]
    texto = mensagem(causa, d["telhado_id"], d["periodo"])  # lança se a causa for desconhecida
    cur = conn.execute(
        "INSERT OR IGNORE INTO acoes (anomalia_id, telhado_id, periodo, causa, acao, mensagem, criado_em) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (d["anomalia_id"], d["telhado_id"], d["periodo"], causa, ACOES[causa], texto, bd.agora()),
    )
    if cur.rowcount:
        print(texto, flush=True)
