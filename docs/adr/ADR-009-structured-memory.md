# ADR-009 — Memória estruturada e local

Status: aceito em 2026-08-24.

## Contexto

Continuidade pessoal exige memória, mas históricos integrais de conversa aumentariam
armazenamento, exposição de dados e carga de consolidação sem garantir significado.

## Decisão

Memórias persistentes são registros semânticos ou episódicos com chave, valor,
importância, confiança, fonte, criação, atualização e expiração. SQLite é a fonte local,
com índices tradicionais e FTS5 para busca. `MemoryService` depende de uma porta e não
do banco.

Working memory é um contêiner limitado à sessão e nunca é persistida. `UserProfile` e
`UserState` continuam modelos separados.

## Consequências

- Nenhum transcript é armazenado.
- Memórias explícitas distinguem-se de inferências pela fonte e confiança.
- Registros expirados não aparecem em recall/listagem/busca e podem ser purgados.
- A busca textual não exige embeddings nem serviços externos.

