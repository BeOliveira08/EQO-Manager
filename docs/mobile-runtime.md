# Mapa de portabilidade móvel v0.8

| Camada | Código atual | Contrato móvel |
|---|---|---|
| Domain | `eqo/domain` | Sem dependência de runtime; entidades e decisões determinísticas |
| Application | `eqo/services`, `eqo/application` | `MobileEQOBackend`, `Scheduler`, `LogicalBackupService` |
| Infrastructure | `eqo/storage`, `eqo/ai`, `eqo/speech` | Adapters substituíveis; SQLite/IA/voz não vazam para os DTOs |
| Interfaces | `eqo/cli`, `mobile/android` | CLI preservada e shell Kotlin como clientes dos casos de uso |

## Fronteira do shell

O dashboard entrega estado atual, uma única próxima ação, quantidade de tarefas e
capabilities. Ações de tarefa, estado e memória usam IDs, enums e primitivos. Conversa e
voz existem na interface, mas podem responder “indisponível” sem afetar o Core. Isso evita
que uma falha de STT, IA ou bridge derrube tarefas e planejamento.

## Persistência e migração

SQLite é detalhe do adapter. A primeira via de migração é exportar entidades para
`.eqobackup` v1; importar será implementado com validação e migração explícitas em uma
versão posterior. Copiar `eqo.db` entre runtimes não é contrato suportado.

## Validação no aparelho

O shell precisa ser compilado e medido em um Galaxy J5 Prime (ou alvo equivalente), em
modo avião, antes de escolher a bridge definitiva. Registrar os resultados usando
`benchmarks/mobile/scenarios.json`. Critérios funcionais: abrir, mostrar “Agora / Próxima
ação”, aceitar texto sem rede e degradar voz quando a permissão for negada.
