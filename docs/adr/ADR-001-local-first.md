# ADR-001 — Arquitetura local-first

Status: aceito em 2026-08-24.

## Decisão

O núcleo funcional do EQO roda sem rede e mantém os dados no dispositivo do usuário.
Integrações remotas futuras serão opcionais e não poderão impedir tarefas, busca ou decisões locais.

## Consequências

- SQLite é a persistência inicial e não requer serviço em background.
- Regras críticas são determinísticas e testáveis.
- IA, sincronização e dispositivos entram por adaptadores substituíveis.

