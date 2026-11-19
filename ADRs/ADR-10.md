#### ADR-10 - Vista local na triagem (lado de leitura do CQRS)

- Contexto: "A triagem guarda a produção e os relatos numa base de dados própria, a partir dos eventos que subscreve (uma vista de leitura, como no CQRS), e não chama outros componentes."
- Decisão: a triagem subscreve `producao.medida` e `relato.recebido` e guarda-os nas tabelas `producao` e `relatos`. O pedido ao modelo é montado só a partir delas.
- Alternativas: pedir os dados ao operacional quando chega uma anomalia. Rejeitada pelo enunciado e porque criaria uma dependência síncrona.
- Consequências: (+) a triagem funciona mesmo com o operacional em baixo. (−) consistência eventual: a vista pode estar atrasada (mitigado pelo ADR-07).
