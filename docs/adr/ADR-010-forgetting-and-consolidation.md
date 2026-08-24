# ADR-010 — Esquecimento físico e consolidação determinística

Status: aceito em 2026-08-24.

## Decisão

`forget` remove fisicamente o registro e sua entrada FTS5. Eventos de auditoria de
criação/esquecimento não copiam chave ou valor. Quando uma memória inferida possui uma
fonte determinística conhecida, esquecer também remove os eventos que poderiam recriá-la.

A primeira consolidação reconhece horário preferido de estudo após no mínimo três
eventos e pelo menos 60% de evidência no mesmo período. O resultado usa `upsert`, evitando
duplicação, e registra confiança proporcional à evidência.

## Consequências

- Uma memória esquecida não reaparece após nova consolidação.
- Não existem tombstones secretos contendo o fato removido.
- Inferências permanecem auditáveis e mais fracas que declarações explícitas.
- Não há event sourcing, LLM ou inferência probabilística no runtime.

