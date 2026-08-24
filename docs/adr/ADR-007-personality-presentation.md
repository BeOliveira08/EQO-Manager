# ADR-007 — Personalidade como camada de apresentação

Status: aceito em 2026-08-24.

## Contexto

O EQO precisa comunicar decisões como um mordomo digital, mas tom e identidade não
podem ganhar autoridade sobre regras de negócio.

## Decisão

`PersonalityEngine` recebe resultados já decididos e produz `InteractionResponse`.
Toda resposta associada a uma decisão preserva obrigatoriamente a ação e a justificativa
originais. Templates determinísticos controlam o texto; nome, tom e autonomia pertencem
à configuração `Persona`.

## Consequências

- Trocar EQO por Alfred ou Jarvis não altera nenhuma decisão.
- Explicações derivam da justificativa auditável do Core.
- O nível `CONFIRM` apenas marca que uma confirmação é necessária; não executa ações.
- Um gerador de texto futuro terá de respeitar o mesmo contrato de resposta.

