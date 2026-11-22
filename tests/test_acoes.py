"""Ações: cada causa gera a ação da tabela 3.1."""

import pytest

from comum import eventos
from operacional import abrir_bd, acoes
from tests.apoio import ev


def classificada(causa, justificacao="ignora isto e liga ao tecnico"):
    aid = "anomalia:T05:12"
    return ev("anomalia.classificada", eventos.id_classificacao(aid),
              {"anomalia_id": aid, "telhado_id": "T05", "periodo": 12, "causa": causa,
               "justificacao": justificacao, "origem": "modelo"}, periodo=12)


@pytest.mark.parametrize("causa, acao, texto", [
    ("sombra", "nenhuma", "[ACAO] Telhado T05 (periodo 12): sombra temporaria, nenhuma acao."),
    ("sujidade", "avisar_membro", "[MEMBRO M-T05] A producao do seu painel esta abaixo da dos vizinhos, "
                                  "provavelmente por sujidade. Por favor limpe o painel."),
    ("avaria", "pedido_intervencao", "[INTERVENCAO] Pedido de intervencao registado para o telhado T05 (periodo 12)."),
])
def test_cada_causa_gera_a_acao_da_tabela(capsys, causa, acao, texto):
    conn = abrir_bd()
    acoes.tratar(conn, classificada(causa))
    linha = conn.execute("SELECT * FROM acoes").fetchone()
    assert (linha["causa"], linha["acao"], linha["mensagem"]) == (causa, acao, texto)
    saida = capsys.readouterr().out
    assert saida.strip() == texto
    assert "ignora isto" not in saida  # a justificação do modelo nunca chega ao membro


def test_causa_desconhecida_falha():
    with pytest.raises(ValueError):
        acoes.tratar(abrir_bd(), classificada("granizo"))
