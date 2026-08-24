# ADR-006 — Planejamento adaptativo somente recomendatório

Status: aceito em 2026-08-24.

## Decisão

O `Planner` recebe tarefas, estado e contexto e devolve um `Plan` imutável. Ele ordena
urgências, respeita o orçamento de tempo e concretiza `REDUCE` como uma alocação menor
e `SPLIT` como segmentos de até 30 minutos.

O plano não persiste, conclui, remove ou reagenda tarefas. Aplicar sugestões exige uma
decisão explícita futura do usuário.

## Consequências

- Planejar é uma operação segura e repetível.
- Conflitos aparecem como trabalho restante ou adiamento, em vez de perda silenciosa.
- Subtarefas persistentes não são necessárias até existir um caso de edição/aplicação.
- A heurística é deliberadamente simples para hardware mínimo e pode evoluir por regras.

