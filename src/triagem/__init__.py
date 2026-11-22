"""Serviço de triagem: vista local, modelo atrás de uma interface, validação, regra sem IA e registo."""

from comum import bd

PRODUTOR = "triagem"
CAUSAS = ("sombra", "sujidade", "avaria")

# Tabelas de dados/triagem.db (ARCHITECTURE 5.5 e 3.6), além de eventos_processados e outbox.
ESQUEMA = """
CREATE TABLE IF NOT EXISTS producao (
    telhado_id  TEXT NOT NULL,
    rua_id      TEXT NOT NULL,
    periodo     INTEGER NOT NULL,
    producao_kw REAL NOT NULL,
    PRIMARY KEY (telhado_id, periodo)
);
CREATE TABLE IF NOT EXISTS relatos (
    relato_id  TEXT PRIMARY KEY,
    telhado_id TEXT NOT NULL,
    membro_id  TEXT NOT NULL,
    periodo    INTEGER NOT NULL,
    texto      TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS decisoes (
    anomalia_id    TEXT PRIMARY KEY,
    modelo         TEXT NOT NULL,
    pedido         TEXT NOT NULL,
    resposta_bruta TEXT,
    valida         INTEGER NOT NULL,
    erro           TEXT,
    causa          TEXT NOT NULL,
    justificacao   TEXT NOT NULL,
    origem         TEXT NOT NULL,
    criado_em      TEXT NOT NULL
);
"""


def abrir_bd(caminho: str = ":memory:"):
    return bd.abrir(caminho, ESQUEMA)
