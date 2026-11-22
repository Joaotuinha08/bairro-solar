"""Regra sem IA, usada quando o modelo falha (ARCHITECTURE 3.5).

O texto dos relatos só pode levar a sombra ou sujidade quando os números também o indicam;
nunca leva diretamente a avaria nem escolhe ações.
"""

import re
import unicodedata

LIMIAR_AVARIA = 0.1
QUEDA_SUBITA = 0.4
EPS = 1e-9

PALAVRAS_OBRA = {"andaime", "grua", "toldo", "obra", "obras", "sombra"}
PALAVRAS_SUJIDADE = {"folha", "folhas", "po", "poeira", "sujo", "suja", "sujidade", "terra"}

JUST_AVARIA_ZERO = "regra sem IA: producao perto de zero"
JUST_SOMBRA = "regra sem IA: queda subita e relato de obra"
JUST_SUJIDADE = "regra sem IA: descida gradual e relato de sujidade"
JUST_DUVIDA = "regra sem IA: sem padrao claro, na duvida avaria"


def normalizar(texto: str) -> str:
    sem_acentos = unicodedata.normalize("NFKD", texto)
    sem_acentos = "".join(c for c in sem_acentos if not unicodedata.combining(c))
    return sem_acentos.lower()


def palavras(texto: str) -> set:
    return set(re.findall(r"[a-z]+", normalizar(texto)))


def racios(pedido: dict) -> list:
    """Lista de (periodo, r) para cada período com dados; r = producao_telhado / media_vizinhos."""
    saida = []
    for periodo, prod, media in zip(
        pedido["periodos"], pedido["producao_telhado_kw"], pedido["media_vizinhos_kw"]
    ):
        if prod is None or media is None or media <= 0:
            continue
        saida.append((periodo, prod / media))
    return saida


def _pares_seguidos(lista: list) -> list:
    """Pares de rácios em períodos seguidos (p, p+1) ambos com dados."""
    return [(a[1], b[1]) for a, b in zip(lista, lista[1:]) if b[0] == a[0] + 1]


def aplicar(pedido: dict) -> tuple:
    """Devolve (causa, justificacao)."""
    lista = racios(pedido)
    periodo_atual = pedido["periodos"][-1]
    r_atual = next((r for p, r in lista if p == periodo_atual), None)

    # 1. produção perto de zero
    if r_atual is not None and r_atual < LIMIAR_AVARIA:
        return "avaria", JUST_AVARIA_ZERO

    pares = _pares_seguidos(lista)
    queda_subita = any(antes - depois >= QUEDA_SUBITA - EPS for antes, depois in pares)
    nunca_sobe = all(depois <= antes + EPS for antes, depois in pares)
    descida_gradual = bool(pares) and nunca_sobe and not queda_subita

    vocab = set()
    for relato in pedido.get("relatos", []):
        vocab |= palavras(relato.get("texto", ""))

    # 2. queda súbita + relato de obra
    if queda_subita and vocab & PALAVRAS_OBRA:
        return "sombra", JUST_SOMBRA
    # 3. descida gradual + relato de sujidade
    if descida_gradual and vocab & PALAVRAS_SUJIDADE:
        return "sujidade", JUST_SUJIDADE
    # 4. na dúvida, avaria
    return "avaria", JUST_DUVIDA
