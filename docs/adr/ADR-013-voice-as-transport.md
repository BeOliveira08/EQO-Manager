# ADR-013 — Voz como transporte explícito e opcional

Status: aceito em 2026-08-24.

## Contexto

Voz precisa reutilizar as mesmas fronteiras de interpretação, confirmação e execução do
texto. Conectar STT diretamente ao domínio criaria um segundo caminho de autoridade.

## Decisão

`VoiceInteractionService` coordena `STT → texto → interpretação → confirmação → Core →
resposta → TTS`. Ele não contém regras de tarefas, estado ou memória. STT só recebe áudio
quando `process` ou `confirm` é chamado explicitamente; não existe captura contínua, wake
word ou serviço de microfone em background.

Whisper e Windows SAPI são adapters opcionais e lazy. Os modos padrão de STT e TTS são
`disabled`, e nenhuma dependência pesada integra o runtime obrigatório.

## Consequências

- Falha de STT não alcança o interpretador nem o Core.
- Falha de TTS preserva a resposta textual completa.
- Confirmações por voz aceitam apenas sim/não/cancela e não retornam ao modelo.
- A mesma camada poderá receber áudio de um botão mobile futuro.

