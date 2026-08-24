# ADR-015 — Fronteira portátil do Core móvel

## Status

Aceita na v0.8.

## Decisão

O domínio e os casos de uso não dependem de CLI, Android, SQLite concreto, STT, TTS ou IA.
`MobileEQOBackend` é a porta de aplicação orientada a snapshots e tipos primitivos. A
implementação Python é uma referência executável, não uma decisão de empacotar Python em APK.
O contrato JSON v1 documenta os campos que adapters em outros runtimes precisam preservar.

## Consequências

O shell Android pode evoluir e ser medido antes da escolha definitiva de integração. Uma
reescrita Kotlin/Rust só será considerada com evidência de gargalo ou incompatibilidade;
alterações incompatíveis exigem nova versão de contrato.
