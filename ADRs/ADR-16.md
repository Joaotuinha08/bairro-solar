#### ADR-16 - Registo de todas as decisões

- Contexto: "Cada decisão fica registada (log ou tabela): o que o modelo recebeu e respondeu." A Aula 10 aponta a observabilidade como característica crítica.
- Decisão: tabela `decisoes` (3.6) mais uma linha na consola.
- Alternativas: só log na consola (perde-se ao reiniciar o contentor).
- Consequências: (+) auditoria e análise de erros do modelo. (−) a base cresce com cada anomalia (irrelevante à escala do trabalho).
