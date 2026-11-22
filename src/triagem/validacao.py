"""Validação da resposta do modelo (ARCHITECTURE 3.4)."""

import json
import re

from triagem import CAUSAS

MAX_JUSTIFICACAO = 500
_BLOCO = re.compile(r"^```[A-Za-z0-9_-]*\s*\n?(.*?)\n?\s*```$", re.DOTALL)


def limpar(texto: str) -> str:
    """Retira espaços e, se existirem, as marcas de bloco de código."""
    texto = texto.strip()
    m = _BLOCO.match(texto)
    if m:
        texto = m.group(1).strip()
    return texto


def validar(texto) -> tuple:
    """Devolve (valida, dados, motivo). `dados` é {'causa', 'justificacao'} quando válida."""
    if not isinstance(texto, str):
        return False, None, "resposta não é texto"
    try:
        obj = json.loads(limpar(texto))
    except json.JSONDecodeError:
        return False, None, "não é JSON"
    if not isinstance(obj, dict):
        return False, None, "não é um objeto JSON"
    chaves = set(obj)
    if chaves != {"causa", "justificacao"}:
        return False, None, f"chaves esperadas causa e justificacao, recebidas {sorted(chaves)}"
    if obj["causa"] not in CAUSAS:
        return False, None, f"causa desconhecida: {obj['causa']!r}"
    just = obj["justificacao"]
    if not isinstance(just, str) or not just.strip():
        return False, None, "justificacao vazia"
    if len(just) > MAX_JUSTIFICACAO:
        return False, None, f"justificacao com {len(just)} caracteres (máximo {MAX_JUSTIFICACAO})"
    return True, {"causa": obj["causa"], "justificacao": just}, None
