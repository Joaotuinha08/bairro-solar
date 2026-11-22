"""Fila op.medicoes: guardar medições, fechar o período, calcular o saldo e detetar anomalias
(ARCHITECTURE 2.6, 3.1 passo 1, 5.6)."""

from comum import bd, eventos
from operacional import PRODUTOR

LIMIAR_ANOMALIA = 0.6   # anómalo se producao <= 0,6 × média dos vizinhos
MIN_VIZINHOS = 3
EPS = 1e-9              # tolerância de vírgula flutuante (exatamente 40% abaixo conta)


def tratar(conn, evento: dict) -> None:
    tipo = evento["tipo"]
    if tipo == "consumo.medido":
        d = evento["dados"]
        _guardar(conn, "consumo", d["casa_id"], None, d["periodo"], d["consumo_kw"])
    elif tipo == "producao.medida":
        d = evento["dados"]
        _guardar(conn, "producao", d["telhado_id"], d["rua_id"], d["periodo"], d["producao_kw"])
    elif tipo == "periodo.encerrado":
        encerrar_periodo(conn, evento)
    else:
        raise ValueError(f"op.medicoes não trata eventos do tipo {tipo!r}")


def _guardar(conn, tipo: str, origem_id: str, rua_id, periodo: int, valor_kw: float) -> None:
    encerrado = conn.execute("SELECT 1 FROM periodos WHERE periodo = ?", (periodo,)).fetchone()
    atrasado = 1 if encerrado else 0
    # segunda proteção contra duplicados: UNIQUE(tipo, origem_id, periodo)
    cur = conn.execute(
        "INSERT OR IGNORE INTO medicoes (tipo, origem_id, rua_id, periodo, valor_kw, atrasado, recebido_em) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (tipo, origem_id, rua_id, periodo, float(valor_kw), atrasado, bd.agora()),
    )
    if atrasado and cur.rowcount:
        print(f"[MEDICOES] valor atrasado guardado para auditoria: {tipo} {origem_id} periodo {periodo}", flush=True)


def encerrar_periodo(conn, evento: dict) -> None:
    periodo = evento["dados"]["periodo"]
    if conn.execute("SELECT 1 FROM periodos WHERE periodo = ?", (periodo,)).fetchone():
        return  # já encerrado; nada já publicado é alterado
    conn.execute("INSERT INTO periodos (periodo, encerrado_em) VALUES (?, ?)", (periodo, bd.agora()))

    # saldo com os valores não atrasados que chegaram antes do fecho
    def total(tipo):
        linha = conn.execute(
            "SELECT COALESCE(SUM(valor_kw), 0) AS soma, COUNT(*) AS n FROM medicoes "
            "WHERE tipo = ? AND periodo = ? AND atrasado = 0",
            (tipo, periodo),
        ).fetchone()
        return round(linha["soma"], 3), linha["n"]

    producao, n_telhados = total("producao")
    consumo, n_casas = total("consumo")
    saldo = round(producao - consumo, 3)
    excedente = saldo > 0
    conn.execute(
        "INSERT INTO saldos (periodo, producao_total_kw, consumo_total_kw, saldo_kw, excedente, n_telhados, n_casas) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (periodo, producao, consumo, saldo, int(excedente), n_telhados, n_casas),
    )
    dados = {
        "periodo": periodo,
        "producao_total_kw": producao,
        "consumo_total_kw": consumo,
        "saldo_kw": saldo,
        "excedente": excedente,
        "n_telhados": n_telhados,
        "n_casas": n_casas,
    }
    bd.outbox_adicionar(conn, eventos.criar_envelope(
        "saldo.calculado", eventos.id_saldo(periodo), dados, PRODUTOR, evento["ocorrido_em"]))
    print(f"[SALDO] periodo {periodo}: producao {producao:.1f} kW, consumo {consumo:.1f} kW, "
          f"saldo {saldo:+.1f} kW ({n_telhados} telhados, {n_casas} casas)", flush=True)

    for anomalia in detetar(conn, periodo, evento["ocorrido_em"]):
        bd.outbox_adicionar(conn, anomalia)


def detetar(conn, periodo: int, ocorrido_em: str) -> list:
    """Compara cada telhado com a média simples dos vizinhos da mesma rua com valor em P.
    Devolve os envelopes producao.anomala (só na passagem de normal a anómalo)."""
    linhas = conn.execute(
        "SELECT origem_id, rua_id, valor_kw FROM medicoes "
        "WHERE tipo = 'producao' AND periodo = ? AND atrasado = 0 ORDER BY origem_id",
        (periodo,),
    ).fetchall()
    por_rua = {}
    for linha in linhas:
        por_rua.setdefault(linha["rua_id"], []).append((linha["origem_id"], linha["valor_kw"]))

    anomalias = []
    for rua_id, telhados in sorted(por_rua.items()):
        for telhado_id, producao in telhados:
            vizinhos = [v for t, v in telhados if t != telhado_id]
            if len(vizinhos) < MIN_VIZINHOS:
                continue
            media = sum(vizinhos) / len(vizinhos)
            if media <= 0:
                continue  # ex.: noite
            anomalo = producao <= LIMIAR_ANOMALIA * media + EPS
            estado = conn.execute(
                "SELECT anomalo FROM estado_telhados WHERE telhado_id = ?", (telhado_id,)
            ).fetchone()
            ja_anomalo = bool(estado and estado["anomalo"])
            if anomalo and not ja_anomalo:
                anomalia_id = eventos.id_anomalia(telhado_id, periodo)
                desvio = round((1 - producao / media) * 100, 1)
                dados = {
                    "anomalia_id": anomalia_id,
                    "telhado_id": telhado_id,
                    "rua_id": rua_id,
                    "periodo": periodo,
                    "producao_kw": round(producao, 3),
                    "media_vizinhos_kw": round(media, 3),
                    "desvio_pct": desvio,
                }
                anomalias.append(eventos.criar_envelope(
                    "producao.anomala", anomalia_id, dados, PRODUTOR, ocorrido_em))
                print(f"[DETECAO] {anomalia_id}: {producao:.2f} kW vs media dos vizinhos {media:.2f} kW "
                      f"({desvio:.1f}% abaixo)", flush=True)
            if anomalo != ja_anomalo:
                conn.execute(
                    "INSERT INTO estado_telhados (telhado_id, anomalo) VALUES (?, ?) "
                    "ON CONFLICT(telhado_id) DO UPDATE SET anomalo = excluded.anomalo",
                    (telhado_id, int(anomalo)),
                )
    return anomalias
