# ADR-008 — Diálogo e interação independentes da CLI

Status: aceito em 2026-08-24.

## Decisão

Onboarding é uma máquina de estados em `DialogueManager`, e não uma sequência de regras
presa ao terminal. Comandos explícitos são convertidos em `Intent` por um parser que
retorna `UNKNOWN` quando não reconhece a entrada, sem adivinhação probabilística.

`InteractionResponse` é neutra quanto ao canal. CLI, voz ou interfaces futuras podem
apresentar o mesmo resultado.

## Consequências

- O fluxo de onboarding pode ser reutilizado por outras interfaces.
- Estados e transições inválidas são testáveis.
- Não existe interpretação de linguagem natural arbitrária na v0.4.
- `AIProvider`, STT e TTS são somente portas; nenhuma implementação integra o runtime.

