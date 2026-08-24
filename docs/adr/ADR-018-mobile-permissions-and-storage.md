# ADR-018 — Permissões e armazenamento móvel

## Status

Aceita para o shell v0.8; criptografia em estudo.

## Decisão

O shell não declara Internet, localização, sensores nem armazenamento compartilhado. Dados
de produção devem residir no armazenamento interno privado. `RECORD_AUDIO` é a única
permissão sensível declarada e é solicitada em runtime somente após tocar em **Falar**;
negação preserva o fluxo textual.

Não será criada criptografia própria. Antes de persistir dados sensíveis, a implementação
deve avaliar Android Keystore e bibliotecas mantidas, com ameaça, recuperação e aparelhos
API 23 documentados.
