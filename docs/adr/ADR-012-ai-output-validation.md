# ADR-012 — Prompt pequeno e validação rígida de saída

Status: aceito em 2026-08-24.

## Decisão

O prompt é construído em um único componente, separando instruções de `USER_DATA`.
Somente até três memórias recuperadas por FTS5 e dois campos do estado atual podem entrar
no contexto inicial. Conteúdo de tarefas ou memória é sempre dado não confiável.

O adapter exige um objeto JSON sem Markdown ou prosa. `AIOutputValidator` verifica intent,
confidence, entidades permitidas/obrigatórias, tipos, tamanhos e valores de domínio.
Reasoning do modelo não é persistido nem usado como justificativa oficial.

Confiança igual ou superior a 0,80 é aceita; entre 0,50 e 0,79 exige confirmação; abaixo
de 0,50 torna-se `UNKNOWN`.

## Consequências

- Intents inventadas e entidades extras são rejeitadas.
- Prompt injection em conteúdo não ganha autoridade estrutural.
- Confiança de interpretação permanece distinta da confiança de uma memória.
- Métricas registram latência, unknown e confirmação sem guardar textos do usuário.

