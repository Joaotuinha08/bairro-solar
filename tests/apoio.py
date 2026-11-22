"""Apoio aos testes: fábricas de eventos e um broker em memória com as filas e bindings da 2.3.

O broker em memória só existe nos testes: encaminha por routing key (padrões topic), mantém a
ordem dentro de cada fila e entrega cada mensagem ao handler genérico (comum.consumidor)."""

from collections import deque
from functools import partial

from comum import broker, consumidor, eventos
from operacional import abrir_bd as abrir_operacional
from operacional.__main__ import EFEITOS
from triagem import abrir_bd as abrir_triagem
from triagem import servico

INICIO = "2026-06-01T10:00:00Z"


def ev(tipo, evento_id, dados, produtor="teste", periodo=0):
    return eventos.criar_envelope(tipo, evento_id, dados, produtor, eventos.ocorrido_em(INICIO, periodo))


def producao(telhado_id, periodo, kw, rua_id="R1", gateway_id="G1"):
    return ev("producao.medida", eventos.id_producao(telhado_id, periodo),
              {"telhado_id": telhado_id, "rua_id": rua_id, "gateway_id": gateway_id,
               "periodo": periodo, "producao_kw": kw}, periodo=periodo)


def consumo(casa_id, periodo, kw, gateway_id="G1"):
    return ev("consumo.medido", eventos.id_consumo(casa_id, periodo),
              {"casa_id": casa_id, "gateway_id": gateway_id, "periodo": periodo, "consumo_kw": kw},
              periodo=periodo)


def encerrado(periodo):
    return ev("periodo.encerrado", eventos.id_periodo(periodo), {"periodo": periodo}, periodo=periodo)


def relato(telhado_id, periodo, texto):
    rid = f"R-{periodo}-{telhado_id}"
    return ev("relato.recebido", eventos.id_relato(rid),
              {"relato_id": rid, "telhado_id": telhado_id, "membro_id": f"M-{telhado_id}",
               "periodo": periodo, "texto": texto}, periodo=periodo)


def corresponde(padrao: str, routing_key: str) -> bool:
    p, k = padrao.split("."), routing_key.split(".")
    if "#" in p:
        raise NotImplementedError
    return len(p) == len(k) and all(a == "*" or a == b for a, b in zip(p, k))


class BrokerMemoria:
    def __init__(self):
        self.filas = {fila: deque() for fila in broker.BINDINGS}
        self.erros = []
        self.publicados = []

    def publicar(self, routing_key: str, corpo: str) -> None:
        self.publicados.append((routing_key, corpo))
        for fila, padroes in broker.BINDINGS.items():
            if any(corresponde(p, routing_key) for p in padroes):
                self.filas[fila].append(corpo)

    def correr(self, consumidores: dict) -> None:
        """consumidores: fila -> (conn, efeito). Entrega até todas as filas ficarem vazias."""
        houve = True
        while houve:
            houve = False
            for fila, (conn, efeito) in consumidores.items():
                if self.filas[fila]:
                    corpo = self.filas[fila].popleft()
                    if consumidor.processar(conn, fila, corpo, efeito, self.publicar) == consumidor.ERRO:
                        self.erros.append((fila, corpo))
                    houve = True


class Sistema:
    """Operacional + triagem ligados ao broker em memória."""

    def __init__(self, modelo):
        self.broker = BrokerMemoria()
        self.op = abrir_operacional()
        self.tr = abrir_triagem()
        self.consumidores = {fila: (self.op, efeito) for fila, efeito in EFEITOS.items()}
        self.consumidores["triagem"] = (self.tr, partial(servico.tratar, modelo=modelo))

    def publicar(self, envelope):
        self.broker.publicar(envelope["tipo"], eventos.serializar(envelope))

    def correr(self):
        self.broker.correr(self.consumidores)
