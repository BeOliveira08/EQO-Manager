# ADR-016 — Shell Android Kotlin separado do Core

## Status

Aceita como experimento arquitetural na v0.8.

## Decisão

Criar um shell Kotlin API 23+ com Views nativas e uma interface `MobileEqoBackend`. Não
converter diretamente o projeto Python em APK. O `ShellPreviewBackend` existe apenas para
validar navegação e deve permanecer identificado como fixture até um adapter persistente.

## Critério para a próxima decisão

Medir startup, memória, armazenamento, planner e busca no aparelho alvo em modo avião.
Escolher IPC, port nativo ou reimplementação somente depois desses dados.
