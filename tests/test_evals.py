"""Os evals com o modelo falso fazem parte dos testes (ARCHITECTURE 6.2)."""

import pytest

from evals import correr

CASOS = correr.carregar_casos()


def test_ha_pelo_menos_os_casos_minimos():
    assert {"sombra", "sujidade", "avaria", "injecao"} <= {c["nome"] for c in CASOS}


@pytest.mark.parametrize("caso", CASOS, ids=[c["nome"] for c in CASOS])
def test_eval_com_modelo_falso(caso):
    r = correr.correr_caso(caso, correr.modelo_falso_do_caso(caso))
    assert r["valida"] == caso["resposta_valida_esperada"], r["erro"]
    assert r["causa_publicada"] == caso["causa_esperada"]


def test_comando_evals_falso_termina_com_sucesso():
    assert correr.main(["--modelo", "falso"]) == 0
