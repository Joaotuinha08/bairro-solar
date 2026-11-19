#### ADR-06 - O período fecha com o que chegou; atrasados só para auditoria

- Contexto: "o período fecha, mesmo que ainda haja valores a caminho" e "valores atrasados são guardados para auditoria, mas não alteram resultados já publicados".
- Decisão: o saldo e a deteção usam só os valores recebidos antes do `periodo.encerrado`. Os que chegam depois são guardados com `atrasado = 1`. Cada período tem um único saldo publicado.
- Alternativas: esperar por todos os valores (bloquearia o sistema por um gateway em baixo); recalcular e republicar o saldo (alteraria resultados já publicados e confundiria o excedente).
- Consequências: (+) resultados estáveis e auditáveis. (−) o saldo de um período com atrasos é calculado com menos valores.
