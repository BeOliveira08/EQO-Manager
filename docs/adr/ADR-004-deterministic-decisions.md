# ADR-004 — Decisões determinísticas e auditáveis

Status: aceito em 2026-08-24.

## Decisão

`DecisionEngine.evaluate` retorna tanto a decisão quanto uma justificativa explícita.
As regras têm precedência definida: estado concluído, prazo, necessidade de descanso,
tempo disponível, capacidade/esforço/flexibilidade e foco.

`recommend` permanece como fachada compatível com a v0.1.

## Consequências

- Uma recomendação pode ser explicada e reproduzida com os mesmos dados.
- LLMs futuros podem interpretar entradas, mas não substituem essas regras.
- Alterações na precedência exigem testes de regressão.

