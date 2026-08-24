# ADR-019 — Scheduler sem autonomia implícita

## Status

Aceita na v0.8.

## Decisão

`Scheduler` agenda, cancela e consulta lembretes; ele não conclui, remove ou replaneja
tarefas. `LocalScheduler` é a referência determinística. `AndroidScheduler` é uma porta do
shell e sua implementação será escolhida após testes de confiabilidade no aparelho alvo.
