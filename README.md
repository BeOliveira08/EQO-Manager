# EQO Core

EQO é um mordomo digital local e adaptativo para administrar tarefas e contexto com
menos carga cognitiva. A versão `0.4.0` evolui o TurboTaskManager existente sem
depender de Internet ou IA generativa.

## Estado da v0.4 — Personality & Interaction Layer

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
