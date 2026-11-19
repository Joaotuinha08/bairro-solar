#### ADR-19 - Simulador por cenários em ficheiros e sem esperas

- Contexto: "a partir de cenários em ficheiros. Escala pequena [...] e sem esperas: os períodos sucedem-se de imediato."
- Decisão: o simulador lê um ficheiro JSON (5.4) e publica os períodos seguidos, sem `sleep`. Duplicados e atrasos são definidos no cenário.
- Alternativas: dados aleatórios em tempo real (resultados não repetíveis e demonstrações demoradas).
- Consequências: (+) cada critério de aceitação tem um cenário que o demonstra de forma repetível. (−) não testa o comportamento com tempo real.

