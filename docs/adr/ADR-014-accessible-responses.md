# ADR-014 — Metadata acessível separada da personalidade

Status: aceito em 2026-08-24.

## Decisão

`InteractionResponse` mantém o texto final e acrescenta prioridade, atenção necessária,
canais permitidos e metadata estruturada. `AccessibilityPresenter` converte esses fatos em
anúncio, alerta visual, vibração e ênfase sem reescrever o texto ou alterar decisões.

Estados de interação — ouvindo, processando, aguardando confirmação, respondendo, erro e
ocioso — são explícitos no `DialogueManager` e podem ser observados pela interface.

## Consequências

- Personalidade continua responsável por “como falar”; acessibilidade, por “como apresentar”.
- Interfaces podem falar, exibir, vibrar ou enfatizar a mesma resposta.
- Uma resposta nunca pode desabilitar simultaneamente fala e exibição.
- A CLI mostra indicadores e métricas quando o modo de voz está habilitado.

