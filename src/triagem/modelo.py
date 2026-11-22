"""Interface do modelo e implementações (ARCHITECTURE 3.3)."""

import json
import os
import re
from typing import Protocol

from triagem import regra

TEMPO_LIMITE_S = 30
GITHUB_BASE_URL = "https://models.github.ai/inference"
MODELO_NOME_POR_DEFEITO = "openai/gpt-4.1-mini"


class ModeloCausas(Protocol):
    nome: str

    def classificar(self, mensagem_sistema: str, mensagem_utilizador: str) -> str:
        """Devolve o texto bruto da resposta. Lança exceção se falhar ou exceder o tempo."""
        ...


class ModeloIndisponivel(RuntimeError):
    """O modelo não respondeu (simulação de modelo em baixo ou configuração em falta)."""


_DADOS = re.compile(r"<dados>\s*(.*?)\s*</dados>", re.DOTALL)


class ModeloFalso:
    """Modelo sem rede, para correr o sistema, os testes e os evals.

    - heuristico: devolve JSON válido com a causa da regra sem IA;
    - fixo: devolve sempre o texto `resposta`;
    - erro: lança ModeloIndisponivel.
    """

    MODOS = ("heuristico", "fixo", "erro")

    def __init__(self, modo: str = "heuristico", resposta: str | None = None):
        if modo not in self.MODOS:
            raise ValueError(f"modo desconhecido: {modo!r}")
        if modo == "fixo" and resposta is None:
            raise ValueError("o modo fixo precisa de uma resposta")
        self.modo = modo
        self.resposta = resposta
        self.nome = f"falso-{modo}"
        self.chamadas = 0

    def classificar(self, mensagem_sistema: str, mensagem_utilizador: str) -> str:
        self.chamadas += 1
        if self.modo == "erro":
            raise ModeloIndisponivel("modelo falso em modo erro (simula modelo em baixo)")
        if self.modo == "fixo":
            return self.resposta
        m = _DADOS.search(mensagem_utilizador)
        if not m:
            raise ValueError("mensagem de utilizador sem bloco <dados>")
        causa, _ = regra.aplicar(json.loads(m.group(1)))
        return json.dumps({"causa": causa, "justificacao": f"modelo falso heuristico: {causa}"},
                          ensure_ascii=False)


class ModeloGitHub:
    """GitHub Models através do SDK openai (temperatura 0, uma tentativa, 30 s)."""

    def __init__(self, nome: str | None = None, token: str | None = None):
        self.nome = nome or os.environ.get("MODELO_NOME") or MODELO_NOME_POR_DEFEITO
        self._token = token if token is not None else os.environ.get("GITHUB_TOKEN", "")
        self._cliente = None

    def _obter_cliente(self):
        if self._cliente is None:
            if not self._token:
                raise ModeloIndisponivel("GITHUB_TOKEN não definido")
            from openai import OpenAI

            self._cliente = OpenAI(
                base_url=GITHUB_BASE_URL, api_key=self._token,
                timeout=TEMPO_LIMITE_S, max_retries=0,
            )
        return self._cliente

    def classificar(self, mensagem_sistema: str, mensagem_utilizador: str) -> str:
        resposta = self._obter_cliente().chat.completions.create(
            model=self.nome,
            temperature=0,
            messages=[
                {"role": "system", "content": mensagem_sistema},
                {"role": "user", "content": mensagem_utilizador},
            ],
        )
        texto = resposta.choices[0].message.content
        if texto is None:
            raise ModeloIndisponivel("resposta sem conteúdo")
        return texto


def criar_modelo(modelo: str | None = None) -> ModeloCausas:
    """Fábrica pela variável MODELO: falso (por defeito), github ou indisponivel."""
    escolha = (modelo or os.environ.get("MODELO") or "falso").strip().lower()
    if escolha == "falso":
        return ModeloFalso("heuristico")
    if escolha == "github":
        return ModeloGitHub()
    if escolha == "indisponivel":
        return ModeloFalso("erro")
    raise ValueError(f"MODELO desconhecido: {escolha!r} (use falso, github ou indisponivel)")
