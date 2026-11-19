#### ADR-09 - Uma base de dados SQLite por serviço

- Contexto: o enunciado pede "um SQLite (ou memória) por serviço".
- Decisão: `dados/operacional.db` e `dados/triagem.db`. Nenhum serviço lê a base de outro.
- Alternativas: base partilhada (acoplaria os serviços pelo esquema); memória (perderia o estado ao reiniciar e não permitiria auditoria).
- Consequências: (+) serviços independentes; SQLite não precisa de servidor. (−) os dados repetem-se entre serviços (ex.: produção existe nas duas bases).
