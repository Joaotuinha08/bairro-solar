"""SQLite de cada serviço: tabelas eventos_processados e outbox (ARCHITECTURE 2.4, 2.5, 5.5)."""

import logging
import os
import sqlite3
from datetime import datetime, timezone

from comum import eventos

log = logging.getLogger(__name__)

TABELAS_COMUNS = """
CREATE TABLE IF NOT EXISTS eventos_processados (
    fila          TEXT NOT NULL,
    evento_id     TEXT NOT NULL,
    processado_em TEXT NOT NULL,
    PRIMARY KEY (fila, evento_id)
);
CREATE TABLE IF NOT EXISTS outbox (
    evento_id   TEXT PRIMARY KEY,
    routing_key TEXT NOT NULL,
    corpo       TEXT NOT NULL,
    publicado   INTEGER NOT NULL DEFAULT 0
);
"""


def agora() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def caminho_bd(nome: str) -> str:
    """Caminho da base dentro de DADOS_DIR (cria a pasta se for preciso)."""
    pasta = os.environ.get("DADOS_DIR", "/app/dados")
    os.makedirs(pasta, exist_ok=True)
    return os.path.join(pasta, nome)


def abrir(caminho: str = ":memory:", esquema: str = "") -> sqlite3.Connection:
    """Abre a base em modo autocommit; as transações são abertas explicitamente (BEGIN)."""
    conn = sqlite3.connect(caminho, isolation_level=None)
    conn.row_factory = sqlite3.Row
    if caminho != ":memory:":
        conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=FULL")
    conn.executescript(TABELAS_COMUNS + esquema)
    return conn


# --- idempotência (2.5) ----------------------------------------------------

def ja_processado(conn: sqlite3.Connection, fila: str, evento_id: str) -> bool:
    linha = conn.execute(
        "SELECT 1 FROM eventos_processados WHERE fila = ? AND evento_id = ?", (fila, evento_id)
    ).fetchone()
    return linha is not None


def marcar_processado(conn: sqlite3.Connection, fila: str, evento_id: str) -> None:
    conn.execute(
        "INSERT INTO eventos_processados (fila, evento_id, processado_em) VALUES (?, ?, ?)",
        (fila, evento_id, agora()),
    )


# --- outbox (2.4) ----------------------------------------------------------

def outbox_adicionar(conn: sqlite3.Connection, envelope: dict) -> None:
    """Chamar dentro da transação que grava o efeito."""
    conn.execute(
        "INSERT OR IGNORE INTO outbox (evento_id, routing_key, corpo, publicado) VALUES (?, ?, ?, 0)",
        (envelope["evento_id"], envelope["tipo"], eventos.serializar(envelope)),
    )


def outbox_pendentes(conn: sqlite3.Connection) -> list:
    return conn.execute(
        "SELECT evento_id, routing_key, corpo FROM outbox WHERE publicado = 0 ORDER BY rowid"
    ).fetchall()


def publicar_outbox(conn: sqlite3.Connection, publicar) -> int:
    """Publica o que está por publicar, por ordem. `publicar(routing_key, corpo)` espera
    a confirmação do broker e lança exceção se falhar. Em caso de falha pára e deixa o resto
    na outbox, para ser publicado na próxima mensagem ou no próximo arranque."""
    publicados = 0
    for linha in outbox_pendentes(conn):
        try:
            publicar(linha["routing_key"], linha["corpo"])
        except Exception as exc:  # noqa: BLE001 - qualquer falha deixa o evento na outbox
            log.warning("outbox: falha a publicar %s (%s); fica para depois", linha["evento_id"], exc)
            break
        conn.execute("UPDATE outbox SET publicado = 1 WHERE evento_id = ?", (linha["evento_id"],))
        publicados += 1
    return publicados
