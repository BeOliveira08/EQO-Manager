# ADR-003 — Interfaces de repositório como portas do Core

Status: aceito em 2026-08-24.

## Contexto

Na v0.1, `TaskService` dependia diretamente de `SQLiteTaskRepository`. Isso ligava a
regra de aplicação ao runtime de persistência e dificultaria testes e clientes futuros.

## Decisão

Os serviços dependem de `Protocol`s estruturais: `TaskRepository`,
`UserStateRepository` e, quando disponível, `BackupRepository`. SQLite implementa
essas portas, mas não faz parte das assinaturas dos serviços.

## Consequências

- O domínio continua sem importar infraestrutura.
- Testes podem usar implementações em memória sem herança obrigatória.
- Android ou outro runtime poderá adaptar persistência sem alterar os serviços.
- Operações exclusivas de migração continuam na borda SQLite/CLI.

