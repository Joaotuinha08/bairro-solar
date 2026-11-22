"""python -m evals.correr --modelo falso|github

falso:  cada caso corre servico.classificar com o ModeloFalso em modo `fixo` (resposta_falsa)
        ou em modo `erro` (resposta_falsa = null, modelo em baixo) e um publicador em memória.
        Verifica (1) se a validação deu o resultado esperado e (2) se a causa publicada é a esperada.
github: corre os mesmos casos uma vez com o modelo real (temperatura 0), ignora resposta_falsa,
        conta as causas certas (X/N) e grava evals/resultados/real-<data>.json.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_RAIZ, "src") not in sys.path:
    sys.path.insert(0, os.path.join(_RAIZ, "src"))

from triagem import servico, vista  # noqa: E402
from triagem.modelo import ModeloFalso, ModeloGitHub  # noqa: E402

PASTA_CASOS = os.path.join(_RAIZ, "evals", "casos")
PASTA_RESULTADOS = os.path.join(_RAIZ, "evals", "resultados")
OCORRIDO_EM = "2026-06-01T10:00:00Z"


def carregar_casos(pasta: str = PASTA_CASOS) -> list:
    casos = []
    for nome in sorted(os.listdir(pasta)):
        if nome.endswith(".json"):
            with open(os.path.join(pasta, nome), encoding="utf-8") as f:
                casos.append(json.load(f))
    return casos


def pedido_do_caso(caso: dict) -> dict:
    a, v = caso["anomalia"], caso["vista"]
    periodos = vista.periodos_janela(a["periodo"])
    n = len(periodos)
    return vista.construir_pedido(
        a["telhado_id"], periodos, v["producao_telhado_kw"][-n:], v["media_vizinhos_kw"][-n:], v["relatos"])


def modelo_falso_do_caso(caso: dict) -> ModeloFalso:
    if caso.get("resposta_falsa") is None:
        return ModeloFalso("erro")
    return ModeloFalso("fixo", caso["resposta_falsa"])


def correr_caso(caso: dict, modelo) -> dict:
    publicados = []  # publicador em memória
    anomalia = caso["anomalia"]
    decisao = servico.classificar(anomalia, pedido_do_caso(caso), modelo)
    publicados.append(servico.criar_evento(anomalia, decisao, OCORRIDO_EM))
    causa_publicada = publicados[-1]["dados"]["causa"]
    return {
        "nome": caso["nome"],
        "modelo": decisao["modelo"],
        "causa_esperada": caso["causa_esperada"],
        "causa_publicada": causa_publicada,
        "causa_certa": causa_publicada == caso["causa_esperada"],
        "valida": decisao["valida"],
        "valida_esperada": caso.get("resposta_valida_esperada"),
        "origem": decisao["origem"],
        "erro": decisao["erro"],
        "resposta_bruta": decisao["resposta_bruta"],
        "justificacao": decisao["justificacao"],
    }


def correr_falso(casos: list) -> tuple:
    resultados = []
    for caso in casos:
        r = correr_caso(caso, modelo_falso_do_caso(caso))
        r["validacao_certa"] = r["valida"] == r["valida_esperada"]
        r["ok"] = r["validacao_certa"] and r["causa_certa"]
        resultados.append(r)
    return resultados, all(r["ok"] for r in resultados)


def correr_github(casos: list) -> tuple:
    modelo = ModeloGitHub()
    resultados = [correr_caso(caso, modelo) for caso in casos]  # um caso de cada vez
    return resultados, modelo.nome


def _linha(r: dict, com_validacao: bool) -> str:
    estado = "OK " if (r["ok"] if com_validacao else r["causa_certa"]) else "ERR"
    valida = f"valida={str(r['valida']).lower():5} (esperada {str(r['valida_esperada']).lower():5}) " if com_validacao \
        else f"valida={str(r['valida']).lower():5} "
    erro = f" | {r['erro']}" if r["erro"] else ""
    return (f"[{estado}] {r['nome']:18} {valida}causa={r['causa_publicada']:8} "
            f"(esperada {r['causa_esperada']:8}) origem={r['origem']}{erro}")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Evals da triagem")
    p.add_argument("--modelo", choices=["falso", "github"], default="falso")
    p.add_argument("--casos", default=PASTA_CASOS)
    args = p.parse_args(argv)
    casos = carregar_casos(args.casos)

    if args.modelo == "falso":
        resultados, tudo_ok = correr_falso(casos)
        for r in resultados:
            print(_linha(r, com_validacao=True))
        n_ok = sum(r["ok"] for r in resultados)
        print(f"\nEvals com o modelo falso: {n_ok}/{len(resultados)} casos certos")
        return 0 if tudo_ok else 1

    resultados, nome = correr_github(casos)
    for r in resultados:
        print(_linha(r, com_validacao=False))
        if not r["causa_certa"] or not r["valida"]:
            print(f"      resposta: {r['resposta_bruta']!r}")
    certas = sum(r["causa_certa"] for r in resultados)
    print(f"\nEvals com {nome}: {certas}/{len(resultados)} causas certas")

    agora = datetime.now(timezone.utc)
    os.makedirs(PASTA_RESULTADOS, exist_ok=True)
    caminho = os.path.join(PASTA_RESULTADOS, f"real-{agora.strftime('%Y-%m-%d')}.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump({
            "modelo": nome,
            "data": agora.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "temperatura": 0,
            "certas": certas,
            "total": len(resultados),
            "resultados": resultados,
        }, f, ensure_ascii=False, indent=2)
    print(f"Resultado gravado em {os.path.relpath(caminho, _RAIZ)} (copiar as conclusões para ARCHITECTURE 3.8)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
