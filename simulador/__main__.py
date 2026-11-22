"""python -m simulador <cenario.json>

Lê um cenário e publica, sem esperas, as medições, os relatos e o fecho de cada período.
Os gateways podem duplicar (mesmo evento_id) ou atrasar (publicar depois do fecho) as medições.
"""

import json
import os
import sys

# permite correr fora do Docker a partir da raiz do repositório
_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_RAIZ, "src") not in sys.path:
    sys.path.insert(0, os.path.join(_RAIZ, "src"))

from comum import eventos  # noqa: E402

PRODUTOR = "simulador"


def carregar_cenario(caminho: str) -> dict:
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def _rua_de(cenario: dict) -> dict:
    return {t: rua for rua, telhados in cenario["ruas"].items() for t in telhados}


def _medicoes_gateway(cenario: dict, gateway_id: str, periodo: int, rua_de: dict) -> list:
    gw = cenario["gateways"][gateway_id]
    quando = eventos.ocorrido_em(cenario["inicio"], periodo)
    mensagens = []
    for casa_id in gw.get("casas", []):
        dados = {
            "casa_id": casa_id,
            "gateway_id": gateway_id,
            "periodo": periodo,
            "consumo_kw": round(float(cenario["consumo_base_kw"]), 3),
        }
        mensagens.append(eventos.criar_envelope(
            "consumo.medido", eventos.id_consumo(casa_id, periodo), dados, PRODUTOR, quando))
    for telhado_id in gw.get("telhados", []):
        fator_t = cenario.get("fatores_telhado", {}).get(telhado_id)
        fator_t = fator_t[periodo] if fator_t is not None else 1
        producao = cenario["producao_base_kw"] * cenario["fator_global"][periodo] * fator_t
        dados = {
            "telhado_id": telhado_id,
            "rua_id": rua_de[telhado_id],
            "gateway_id": gateway_id,
            "periodo": periodo,
            "producao_kw": round(producao, 3),
        }
        mensagens.append(eventos.criar_envelope(
            "producao.medida", eventos.id_producao(telhado_id, periodo), dados, PRODUTOR, quando))
    return mensagens


def gerar_mensagens(cenario: dict) -> list:
    """Devolve a lista ordenada de envelopes a publicar (a routing key é o `tipo`)."""
    rua_de = _rua_de(cenario)
    duplicados = {(d["gateway"], d["periodo"]) for d in cenario.get("duplicados", [])}
    atrasos = {(a["gateway"], a["periodo"]) for a in cenario.get("atrasos", [])}
    saida = []
    for p in range(cenario["periodos"]):
        quando = eventos.ocorrido_em(cenario["inicio"], p)
        atrasadas = []
        # 1. medições de cada gateway (duplicadas ou guardadas para depois do fecho)
        for gateway_id in cenario["gateways"]:
            medicoes = _medicoes_gateway(cenario, gateway_id, p, rua_de)
            repeticoes = 2 if (gateway_id, p) in duplicados else 1
            if (gateway_id, p) in atrasos:
                atrasadas.extend(m for m in medicoes for _ in range(repeticoes))
            else:
                saida.extend(m for m in medicoes for _ in range(repeticoes))
        # 2. relatos do período
        for relato in cenario.get("relatos", []):
            if relato["periodo"] != p:
                continue
            telhado_id = relato["telhado"]
            relato_id = f"R-{p}-{telhado_id}"
            dados = {
                "relato_id": relato_id,
                "telhado_id": telhado_id,
                "membro_id": f"M-{telhado_id}",
                "periodo": p,
                "texto": relato["texto"],
            }
            saida.append(eventos.criar_envelope(
                "relato.recebido", eventos.id_relato(relato_id), dados, PRODUTOR, quando))
        # 3. fecho do período
        saida.append(eventos.criar_envelope(
            "periodo.encerrado", eventos.id_periodo(p), {"periodo": p}, PRODUTOR, quando))
        # 4. medições atrasadas
        saida.extend(atrasadas)
    return saida


def main(argv: list) -> int:
    if len(argv) != 1:
        print("uso: python -m simulador <cenario.json>", file=sys.stderr)
        return 2
    cenario = carregar_cenario(argv[0])
    mensagens = gerar_mensagens(cenario)

    from comum import broker

    conexao = broker.ligar()
    canal = conexao.channel()
    broker.declarar_topologia(canal)  # garante que as filas existem antes de publicar
    publicar = broker.Publicador(canal, canal_proprio=False)  # um único canal com confirms

    contagem = {}
    for envelope in mensagens:
        publicar(envelope["tipo"], eventos.serializar(envelope))
        contagem[envelope["tipo"]] = contagem.get(envelope["tipo"], 0) + 1
    conexao.close()

    resumo = ", ".join(f"{tipo}={n}" for tipo, n in sorted(contagem.items()))
    print(f"[SIMULADOR] cenario '{cenario['nome']}': {len(mensagens)} mensagens publicadas ({resumo})", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
