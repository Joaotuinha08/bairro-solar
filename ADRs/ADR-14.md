#### ADR-14 - Modelo atrás de uma interface, com modelo falso

- Contexto: "O modelo fica atrás de uma interface, com um modelo falso para os testes." Os evals correm com o modelo falso.
- Decisão: interface `ModeloCausas` (3.3) com `ModeloGitHub` e `ModeloFalso`, escolhidos pela variável `MODELO`.
- Alternativas: chamar a API diretamente no código da triagem. Rejeitada porque os testes dependeriam da rede e não seriam repetíveis.
- Consequências: (+) testes rápidos e determinísticos; trocar de fornecedor é uma nova implementação. (−) o modelo falso não prova a qualidade do modelo real (para isso servem os evals com o modelo real).