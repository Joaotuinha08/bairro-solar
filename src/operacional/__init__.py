"""Serviço operacional (sem IA): medições, saldo, deteção, excedente, aviso, painel e ações."""

from comum import bd

PRODUTOR = "operacional"

# Tabelas de dados/operacional.db (ARCHITECTURE 5.5), além de eventos_processados e outbox.
ESQUEMA = """
CREATE TABLE IF NOT EXISTS medicoes (
    tipo        TEXT NOT NULL,          -- 'consumo' ou 'producao'
    origem_id   TEXT NOT NULL,          -- casa_id ou telhado_id
    rua_id      TEXT,                   -- só na produção
    periodo     INTEGER NOT NULL,
    valor_kw    REAL NOT NULL,
    atrasado    INTEGER NOT NULL,
    recebido_em TEXT NOT NULL,
    UNIQUE (tipo, origem_id, periodo)
);
CREATE TABLE IF NOT EXISTS periodos (
    periodo      INTEGER PRIMARY KEY,
    encerrado_em TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS saldos (
    periodo           INTEGER PRIMARY KEY,
    producao_total_kw REAL NOT NULL,
    consumo_total_kw  REAL NOT NULL,
    saldo_kw          REAL NOT NULL,
    excedente         INTEGER NOT NULL,
    n_telhados        INTEGER NOT NULL,
    n_casas           INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS estado_excedente (
    id             INTEGER PRIMARY KEY CHECK (id = 1),
    ativo          INTEGER NOT NULL,
    ultimo_periodo INTEGER NOT NULL
);
INSERT OR IGNORE INTO estado_excedente (id, ativo, ultimo_periodo) VALUES (1, 0, -1);
CREATE TABLE IF NOT EXISTS estado_telhados (
    telhado_id TEXT PRIMARY KEY,
    anomalo    INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS painel (
    periodo      INTEGER NOT NULL,
    tipo         TEXT NOT NULL,         -- 'iniciado' ou 'terminado'
    saldo_kw     REAL NOT NULL,
    registado_em TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS acoes (
    anomalia_id TEXT PRIMARY KEY,
    telhado_id  TEXT NOT NULL,
    periodo     INTEGER NOT NULL,
    causa       TEXT NOT NULL,
    acao        TEXT NOT NULL,
    mensagem    TEXT NOT NULL,
    criado_em   TEXT NOT NULL
);
"""


def abrir_bd(caminho: str = ":memory:"):
    return bd.abrir(caminho, ESQUEMA)
