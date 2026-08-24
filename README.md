# EQO Core

EQO é um mordomo digital local e adaptativo para administrar tarefas e contexto com
menos carga cognitiva. A versão `0.8.0` evolui o TurboTaskManager existente sem
depender de Internet ou IA generativa.

## Estado da v0.8 — Mobile Runtime Boundary

- fachada `MobileEQOBackend` orientada a estado e próxima ação, sem tipos de SQLite ou CLI;
- implementação Python de referência para provar a portabilidade dos casos de uso;
- contrato JSON versionado para manter adapters de runtimes diferentes compatíveis;
- exportação lógica `.eqobackup` versionada pelas entidades, sem copiar o banco;
- `Scheduler` abstrato e `LocalScheduler` determinístico, sem autonomia sobre tarefas;
- shell Android Kotlin API 23+ sem Python embarcado e sem permissão de Internet;
- microfone solicitado apenas após a ação explícita **Falar**, com fallback textual;
- protocolo de benchmark mobile para startup, RAM, banco, planner, busca, IA e voz;
- shell claramente marcado como demonstrativo até receber um backend persistente;
- ADRs de fronteira mobile, backup, scheduler e segurança/permissões.

## Base preservada da v0.7 — Voice & Accessibility Layer

- domínio de tarefas separado da interface;
- persistência local SQLite e importação não destrutiva do `tasks.json` legado;
- criação, filtros, busca, conclusão, remoção, prazos, estatísticas e backups automáticos;
- `UserState` e primeiro `DecisionEngine` determinístico;
- CLI compatível com `python main.py` e testes automatizados do núcleo.
- serviços desacoplados do SQLite por interfaces de repositório;
- `UserState` persistente com capacidade, energia, tempo, foco e estresse;
- decisões auditáveis para executar, adiar, reduzir, dividir, descansar e considerar;
- regressões de ordenação e fluxo completo da CLI cobertas por testes.
- contexto explícito com horário, dia, disponibilidade e atividade atual;
- planejamento recomendatório que não modifica tarefas;
- ordenação por urgência, conflitos de tempo, redução e divisão em segmentos;
- atualização de estado e plano sugerido disponíveis na CLI pelas opções 10 e 11.
- persona determinística separada das decisões e do planejamento;
- perfil persistente com nome do usuário, assistente, idioma e fuso horário;
- onboarding por máquina de estados e troca do nome do assistente;
- respostas auditáveis que preservam decisão e justificativa do Core;
- intents e parser de comandos explícitos, sem interpretação livre ou LLM;
- fronteiras opcionais para IA, STT e TTS sem implementações ou dependências pesadas.
- memória semântica e episódica estruturada em SQLite, sem histórico de chat;
- working memory limitada à sessão e separada da persistência;
- importância, confiança, fonte e expiração em cada memória;
- busca local com SQLite FTS5;
- esquecimento físico, incluindo evidência capaz de recriar uma inferência;
- consolidação determinística de padrões sem duplicação;
- CLI para lembrar, listar e esquecer pelas opções 14, 15 e 16.
- `AIRequest` e `AIInterpretation` estritamente tipados;
- validator de intent, confidence, entidades, tipos, tamanhos e valores;
- thresholds explícitos para aceitar, confirmar ou retornar `UNKNOWN`;
- contexto mínimo com no máximo três memórias recuperadas por FTS5;
- `OllamaAIProvider` opcional, isolado e sem dependência Python adicional;
- fallback seguro para timeout, indisponibilidade e saída inválida;
- executor que só aceita interpretações confirmadas pelo pipeline;
- primeira suíte de frases em `benchmarks/intent_cases.json`;
- opção 17 da CLI para linguagem natural quando o modo local estiver habilitado.
- protocolos substituíveis de STT e TTS;
- `VoiceInteractionService` sem regras de negócio;
- estados explícitos de escuta, processamento, confirmação, resposta e erro;
- confirmação falada determinística sem nova chamada à IA;
- respostas com prioridade, atenção e metadata de acessibilidade;
- falhas isoladas: STT/TTS/IA não derrubam texto nem Core;
- métricas locais de STT, interpretação, Core, TTS e latência total;
- benchmark de voz em `benchmarks/voice_cases.json`;
- opção 18 para processar um WAV iniciado explicitamente pelo usuário.

## Inteligência local opcional

O modo padrão permanece desligado. Para usar um Ollama já instalado e em execução:

```powershell
$env:EQO_AI_MODE = "local"
$env:EQO_OLLAMA_MODEL = "llama3.2:3b"
eqo
```

Também podem ser definidos `EQO_OLLAMA_HOST` e `EQO_AI_TIMEOUT`. Se o Ollama estiver
indisponível, o EQO retorna `UNKNOWN` e mantém o Core funcional.

## Voz opcional

Voz permanece desligada por padrão. Para experimentar Whisper local e SAPI no Windows:

```powershell
$env:EQO_STT_MODE = "whisper"
$env:EQO_WHISPER_MODEL = "tiny"
$env:EQO_TTS_MODE = "windows"
eqo
```

O pacote Whisper não é instalado pelo EQO e deve ser fornecido separadamente no ambiente
de desenvolvimento. A opção 18 aceita um WAV capturado após uma ação explícita do usuário;
não há escuta contínua. Sem STT ou TTS, todas as interfaces textuais permanecem funcionais.

## Executar e verificar

Requer Python 3.12+.

```powershell
python -m pip install -e ".[dev]"
python main.py
python -m pytest
python -m ruff check .
python -m mypy src/eqo
```

O banco é criado em `data/eqo.db`. Se existir `tasks.json` e o banco estiver vazio,
as tarefas são importadas uma única vez; o JSON não é alterado. As decisões estão
registradas em [`docs/adr`](docs/adr).

---

## Histórico: Turbo Task Manager CLI (Python)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Version-2.0-brightgreen)

**Um gerenciador de tarefas avançado para terminal** com prioridades, prazos, buscas inteligentes e sistema de backups.

## Features Premium

**Prioridades** (Alta/Média/Baixa)  
**Prazos com alertas** (Atrasadas/Hoje)  
**Busca inteligente** por palavras-chave  
**Backup automático** das tarefas  
**Estatísticas completas**  
**Filtros avançados** (Todas/Concluídas/Pendentes)  
**Interface colorida** intuitiva  

##  Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/super-task-manager.git
cd super-task-manager

# Instale as dependências
pip install -r requirements.txt
```

 **Requisitos**: Python 3.8+ | Colorama (instalado automaticamente)

##  Como Usar

```bash
python super_task_manager.py
```

**Menu Principal:**
```
1. Adicionar tarefa
2. Listar todas
3. Listar concluídas
4. Listar pendentes
5. Buscar tarefas
6. Concluir tarefa
7. Remover tarefa
8. Estatísticas
9. Sair
```

##  Estrutura do Projeto

```
super-task-manager/
├── super_task_manager.py  # Código principal
├── tasks.json            # Banco de dados das tarefas
├── backups/              # Pasta de backups automáticos
│   └── tasks_backup_*.json
├── requirements.txt      # Dependências
└── README.md            # Este arquivo
```

##  Funcionalidades Detalhadas

###  Sistema de Prazos
- Visualização de dias restantes
- Alertas coloridos para tarefas:
  -  `[ATRASADA]`
  -  `[HOJE]`
  -  `(3d)` - dias restantes

###  Prioridades
```python
PRIORITIES = {
    "1": {"name": "Alta", "color": Fore.RED},
    "2": {"name": "Média", "color": Fore.YELLOW},
    "3": {"name": "Baixa", "color": Fore.GREEN}
}
```

###  Busca Inteligente
```bash
[Buscar tarefas]
Termo de busca: estudar
```

###  Estatísticas
```
 Estatísticas:
• Total: 5 tarefas
• Concluídas: 2
• Pendentes: 3
• Alta: 1
• Média: 2
• Baixa: 2
```

## Sistema de Backup
Backups automáticos são salvos em:
```bash
backups/
├── tasks_backup_20230815_143022.json
└── tasks_backup_20230816_101512.json
```

## Como Contribuir
1. Faça um Fork
2. Crie uma Branch (`git checkout -b feature/nova-feature`)
3. Commit (`git commit -m 'Add nova feature'`)
4. Push (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## Licença
MIT - Distribuído livremente

##  Contato
Bernardo Oliveira - bernardocher22@gmail.com

--- 

** Link do Projeto**: https://github.com/BeOliveira08/TurboTaskManager

>**Dica**: Execute com `python -i super_task_manager.py` para modo interativo!

---

### Capturas de Tela (Adicione URLs reais)
1. **Menu Principal**: `![Menu](url-da-imagem)`
2. **Lista de Tarefas**: `![Tasks](url-da-imagem)`
3. **Estatísticas**: `![Stats](url-da-imagem)`
