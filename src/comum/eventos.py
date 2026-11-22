"""Envelope comum dos eventos (ARCHITECTURE 2.1) e ids determinísticos (2.2)."""

import json
from datetime import datetime, timedelta, timezone

VERSAO = 1
DURACAO_PERIODO = timedelta(minutes=15)
CAMPOS_ENVELOPE = ("evento_id", "tipo", "versao", "ocorrido_em", "produtor", "dados")


# --- ids determinísticos (tabela 2.2) -------------------------------------

def id_consumo(casa_id: str, periodo: int) -> str:
    return f"consumo:{casa_id}:{periodo}"


def id_producao(telhado_id: str, periodo: int) -> str:
    return f"producao:{telhado_id}:{periodo}"


def id_relato(relato_id: str) -> str:
    return f"relato:{relato_id}"


def id_periodo(periodo: int) -> str:
    return f"periodo:{periodo}"


def id_saldo(periodo: int) -> str:
    return f"saldo:{periodo}"


def id_excedente(periodo: int, acontecimento: str) -> str:
    """acontecimento: 'iniciado' ou 'terminado'."""
    return f"excedente:{periodo}:{acontecimento}"


def id_anomalia(telhado_id: str, periodo: int) -> str:
    return f"anomalia:{telhado_id}:{periodo}"


def id_classificacao(anomalia_id: str) -> str:
    return f"classificacao:{anomalia_id}"


# --- tempo simulado -------------------------------------------------------

def ocorrido_em(inicio: str, periodo: int) -> str:
    """Início do período em tempo simulado: início do cenário + 15 min × período, em UTC."""
    base = datetime.fromisoformat(inicio.replace("Z", "+00:00")).astimezone(timezone.utc)
    return (base + periodo * DURACAO_PERIODO).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- envelope -------------------------------------------------------------

def criar_envelope(tipo: str, evento_id: str, dados: dict, produtor: str, ocorrido_em: str) -> dict:
    return {
        "evento_id": evento_id,
        "tipo": tipo,
        "versao": VERSAO,
        "ocorrido_em": ocorrido_em,
        "produtor": produtor,
        "dados": dados,
    }


def serializar(envelope: dict) -> str:
    return json.dumps(envelope, ensure_ascii=False)


def ler_evento(corpo) -> dict:
    """Lê e valida o envelope. Lança ValueError se não for um evento válido."""
    if isinstance(corpo, (bytes, bytearray)):
        corpo = corpo.decode("utf-8")
    try:
        evento = json.loads(corpo)
    except json.JSONDecodeError as exc:
        raise ValueError(f"corpo não é JSON: {exc}") from exc
    if not isinstance(evento, dict):
        raise ValueError("evento não é um objeto JSON")
    em_falta = [c for c in CAMPOS_ENVELOPE if c not in evento]
    if em_falta:
        raise ValueError(f"envelope sem campos: {', '.join(em_falta)}")
    if not isinstance(evento["dados"], dict):
        raise ValueError("'dados' não é um objeto")
    if not isinstance(evento["evento_id"], str) or not evento["evento_id"]:
        raise ValueError("'evento_id' inválido")
    return evento
