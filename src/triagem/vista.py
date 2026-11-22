"""Vista local da triagem (CQRS): guardada a partir dos eventos e usada para montar o pedido
ao modelo (ARCHITECTURE 3.2, 5.6). A triagem nunca pergunta nada a outro serviço."""

JANELA = 4          # última hora: P-3 a P
MAX_RELATOS = 3


def guardar_producao(conn, dados: dict) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO producao (telhado_id, rua_id, periodo, producao_kw) VALUES (?, ?, ?, ?)",
        (dados["telhado_id"], dados["rua_id"], dados["periodo"], float(dados["producao_kw"])),
    )


def guardar_relato(conn, dados: dict) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO relatos (relato_id, telhado_id, membro_id, periodo, texto) VALUES (?, ?, ?, ?, ?)",
        (dados["relato_id"], dados["telhado_id"], dados["membro_id"], dados["periodo"], dados["texto"]),
    )


def periodos_janela(periodo: int) -> list:
    return list(range(max(0, periodo - JANELA + 1), periodo + 1))


def construir_pedido(telhado_id: str, periodos: list, producao: list, medias: list, relatos: list) -> dict:
    return {
        "telhado_id": telhado_id,
        "periodos": list(periodos),
        "producao_telhado_kw": list(producao),
        "media_vizinhos_kw": list(medias),
        "relatos": [{"periodo": r["periodo"], "texto": r["texto"]} for r in relatos],
    }


def montar_pedido(conn, telhado_id: str, rua_id: str, periodo: int) -> dict:
    periodos = periodos_janela(periodo)
    producao, medias = [], []
    for p in periodos:
        linha = conn.execute(
            "SELECT producao_kw FROM producao WHERE telhado_id = ? AND periodo = ?", (telhado_id, p)
        ).fetchone()
        producao.append(round(linha["producao_kw"], 3) if linha else None)
        media = conn.execute(
            "SELECT AVG(producao_kw) AS m FROM producao WHERE rua_id = ? AND periodo = ? AND telhado_id != ?",
            (rua_id, p, telhado_id),
        ).fetchone()["m"]
        medias.append(round(media, 3) if media is not None else None)
    relatos = conn.execute(
        "SELECT periodo, texto FROM relatos WHERE telhado_id = ? AND periodo <= ? "
        "ORDER BY periodo DESC, relato_id DESC LIMIT ?",
        (telhado_id, periodo, MAX_RELATOS),
    ).fetchall()
    relatos = [dict(r) for r in reversed(relatos)]  # do mais antigo para o mais recente
    return construir_pedido(telhado_id, periodos, producao, medias, relatos)
