#### ADR-08 - Payload com os dados completos

- Contexto: a Aula 8 compara eventos só com a chave e eventos com os dados.
- Decisão: cada evento leva os dados de que os consumidores precisam (ex.: `producao.medida` leva `rua_id`; `producao.anomala` leva a média e o desvio).
- Alternativas: só a chave, obrigando o consumidor a perguntar ao produtor. Rejeitada porque a triagem não pode chamar outros componentes (regra 1 da triagem) e criaria acoplamento síncrono.
- Consequências: (+) consumidores autónomos, sem consultas a outros serviços. (−) contratos maiores; mudar um campo obriga a mudar a `versao` do evento.
