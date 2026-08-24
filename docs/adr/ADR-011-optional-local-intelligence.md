# ADR-011 — Inteligência local opcional e substituível

Status: aceito em 2026-08-24.

## Contexto

O EQO precisa interpretar linguagem menos rígida sem transferir autoridade sobre tarefas,
estado ou memória para um modelo probabilístico.

## Decisão

`AIProvider` recebe `AIRequest` e retorna `AIInterpretation` estruturada. O modo padrão é
`DISABLED`; `LOCAL` habilita o adapter Ollama pela borda HTTP. Nenhuma biblioteca ou
servidor de IA é dependência do Core, e comandos determinísticos têm precedência.

O provider nunca recebe serviços ou repositórios. Uma interpretação somente alcança
`InterpretationExecutor` depois da política de confiança e, quando necessário, de uma
confirmação atual do usuário.

## Consequências

- Remover Ollama não afeta tarefas, planejamento, memória ou CLI.
- O runtime de desenvolvimento pode ser trocado por um runtime mobile futuro.
- Indisponibilidade, timeout e saída inválida convertem-se em `UNKNOWN`, sem mutação.
- O modelo classifica intenções; respostas continuam sob controle da personalidade.

