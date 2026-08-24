# ADR-002 — SQLite como persistência local

Status: aceito em 2026-08-24.

## Decisão

O EQO Core v0.1 usa SQLite. Na primeira execução, um `tasks.json` legado é importado
somente quando o banco está vazio. O arquivo original permanece intacto como fallback.

## Consequências

- A migração é reversível e não destrói os dados legados.
- O esquema pode crescer incrementalmente e adotar FTS5 quando a busca justificar isso.

