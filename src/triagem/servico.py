"""Classificar uma anomalia (usado pelo serviço e pelos evals) e efeito da fila `triagem`
(ARCHITECTURE 3.1 passo 2, 3.4-3.7, 5.6)."""

import json
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout

from comum import bd, eventos
from triagem import PRODUTOR, prompt, regra, validacao, vista
from triagem.modelo import TEMPO_LIMITE_S


def _chamar_com_limite(modelo, sistema: str, utilizador: str, limite_s: float) -> str:
    """Uma única tentativa, com tempo limite independente da implementação do modelo."""
    executor = ThreadPoolExecutor(max_workers=1)
    futuro = executor.submit(modelo.classificar, sistema, utilizador)
    try:
        return futuro.result(timeout=limite_s)
    except FuturesTimeout as exc:
        raise TimeoutError(f"modelo não respondeu em {limite_s} s") from exc
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def classificar(anomalia: dict, pedido: dict, modelo, limite_s: float = TEMPO_LIMITE_S) -> dict:
    """Pergunta a causa ao modelo, valida e, se preciso, aplica a regra sem IA.
    Devolve a decisão com todos os campos da tabela `decisoes` (exceto criado_em)."""
    sistema = prompt.SISTEMA
    utilizador = prompt.mensagem_utilizador(pedido)
    resposta, erro, valida = None, None, False
    causa = justificacao = None

    try:
        resposta = _chamar_com_limite(modelo, sistema, utilizador, limite_s)
    except Exception as exc:  # noqa: BLE001 - qualquer falha do modelo leva à regra
        erro = f"{type(exc).__name__}: {exc}"

    if resposta is not None:
        valida, dados, motivo = validacao.validar(resposta)
        if valida:
            causa, justificacao = dados["causa"], dados["justificacao"]
        else:
            erro = f"resposta invalida: {motivo}"

    if valida:
        origem = "modelo"
    else:
        causa, justificacao = regra.aplicar(pedido)
        origem = "regra"

    return {
        "anomalia_id": anomalia["anomalia_id"],
        "modelo": getattr(modelo, "nome", type(modelo).__name__),
        "pedido": json.dumps({"sistema": sistema, "utilizador": utilizador}, ensure_ascii=False),
        "resposta_bruta": resposta if isinstance(resposta, str) or resposta is None else str(resposta),
        "valida": valida,
        "erro": erro,
        "causa": causa,
        "justificacao": justificacao,
        "origem": origem,
    }


def criar_evento(anomalia: dict, decisao: dict, ocorrido_em: str) -> dict:
    dados = {
        "anomalia_id": anomalia["anomalia_id"],
        "telhado_id": anomalia["telhado_id"],
        "periodo": anomalia["periodo"],
        "causa": decisao["causa"],
        "justificacao": decisao["justificacao"],
        "origem": decisao["origem"],
    }
    return eventos.criar_envelope(
        "anomalia.classificada", eventos.id_classificacao(anomalia["anomalia_id"]),
        dados, PRODUTOR, ocorrido_em)


def gravar_decisao(conn, decisao: dict) -> None:
    conn.execute(
        "INSERT INTO decisoes (anomalia_id, modelo, pedido, resposta_bruta, valida, erro, causa, "
        "justificacao, origem, criado_em) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (decisao["anomalia_id"], decisao["modelo"], decisao["pedido"], decisao["resposta_bruta"],
         int(decisao["valida"]), decisao["erro"], decisao["causa"], decisao["justificacao"],
         decisao["origem"], bd.agora()),
    )


def tratar(conn, evento: dict, modelo) -> None:
    """Efeito da fila `triagem`."""
    tipo, d = evento["tipo"], evento["dados"]
    if tipo == "producao.medida":
        vista.guardar_producao(conn, d)
    elif tipo == "relato.recebido":
        vista.guardar_relato(conn, d)
    elif tipo == "producao.anomala":
        pedido = vista.montar_pedido(conn, d["telhado_id"], d["rua_id"], d["periodo"])
        decisao = classificar(d, pedido, modelo)
        gravar_decisao(conn, decisao)
        bd.outbox_adicionar(conn, criar_evento(d, decisao, evento["ocorrido_em"]))
        extra = f" [{decisao['erro']}]" if decisao["erro"] else ""
        print(f"[TRIAGEM] {d['anomalia_id']} -> {decisao['causa']} (origem: {decisao['origem']}){extra}", flush=True)
    else:
        raise ValueError(f"triagem não trata eventos do tipo {tipo!r}")
