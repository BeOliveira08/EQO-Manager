# ADR-005 — Contexto explícito e relógio injetável

Status: aceito em 2026-08-24.

## Contexto

Planejamento não pode depender implicitamente do relógio do sistema ou de sensores.
Isso tornaria decisões difíceis de reproduzir e testaria apenas o instante corrente.

## Decisão

`Context` é um valor imutável com horário timezone-aware, dia da semana derivado,
minutos disponíveis e atividade opcional. `ContextEngine` recebe um relógio injetável
e usa `UserState` como origem padrão da disponibilidade.

Sensores, localização e calendários não fazem parte desta versão.

## Consequências

- Um plano pode ser reproduzido passando o mesmo contexto.
- Não há risco de `current_time` e `day_of_week` divergirem.
- Interfaces futuras podem produzir o mesmo modelo sem entrar no domínio.

