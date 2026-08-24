from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from colorama import Fore, init  # type: ignore[import-untyped]

from eqo.domain.task import Priority, Task, TaskStatus
from eqo.services.task_service import TaskService
from eqo.storage.sqlite_repository import SQLiteTaskRepository

init(autoreset=True)


def _render_tasks(tasks: list[Task], today: date | None = None) -> None:
    if not tasks:
        print(Fore.YELLOW + "Nenhuma tarefa encontrada.")
        return
    current_date = today or date.today()
    for index, task in enumerate(tasks, 1):
        status = Fore.GREEN + "[x]" if task.completed else Fore.RED + "[ ]"
        deadline = ""
        if task.deadline:
            days_left = (task.deadline - current_date).days
            if days_left < 0:
                suffix = " [ATRASADA]"
            elif days_left == 0:
                suffix = " [HOJE]"
            else:
                suffix = f", {days_left}d"
            deadline = Fore.BLUE + f" (Prazo: {task.deadline.isoformat()}{suffix})"
        print(f"{index}. {status} [{task.priority.label}] {task.title}{deadline}")


class CLI:
    def __init__(self, service: TaskService) -> None:
        self.service = service

    def run(self) -> None:
        while True:
            print(Fore.BLUE + "\n--- EQO ---")
            print("1. Adicionar tarefa\n2. Listar todas\n3. Listar concluídas")
            print("4. Listar pendentes\n5. Buscar tarefas\n6. Concluir tarefa")
            print("7. Remover tarefa\n8. Estatísticas\n9. Sair")
            choice = input(Fore.CYAN + "Escolha: ").strip()
            actions = {
                "1": self.add_task, "2": lambda: self.list_tasks(),
                "3": lambda: self.list_tasks(TaskStatus.COMPLETED),
                "4": lambda: self.list_tasks(TaskStatus.PENDING), "5": self.search_tasks,
                "6": lambda: self.manage_task("concluir"),
                "7": lambda: self.manage_task("remover"), "8": self.show_stats,
            }
            if choice == "9":
                print(Fore.MAGENTA + "Até logo!")
                return
            action = actions.get(choice)
            if action:
                action()
            else:
                print(Fore.RED + "Opção inválida!")

    def add_task(self) -> None:
        title = input(Fore.CYAN + "Título da tarefa: ").strip()
        if not title:
            print(Fore.YELLOW + "O título não pode estar vazio!")
            return
        raw = input(Fore.CYAN + "Prioridade (1-Alta, 2-Média, 3-Baixa): ").strip() or "2"
        try:
            priority = Priority(int(raw))
        except ValueError:
            print(Fore.YELLOW + "Prioridade inválida; usando Média.")
            priority = Priority.MEDIUM
        deadline = None
        if input("Adicionar prazo? (s/n): ").strip().casefold() == "s":
            try:
                raw_deadline = input("Data (YYYY-MM-DD): ").strip()
                deadline = datetime.strptime(raw_deadline, "%Y-%m-%d").date()
            except ValueError:
                print(Fore.RED + "Formato de data inválido; tarefa criada sem prazo.")
        self.service.create(title, priority, deadline)
        print(Fore.GREEN + "OK: Tarefa adicionada!")

    def list_tasks(self, status: TaskStatus | None = None) -> None:
        _render_tasks(self.service.list(status))

    def search_tasks(self) -> None:
        _render_tasks(self.service.search(input(Fore.CYAN + "Termo de busca: ")))

    def manage_task(self, action: str) -> None:
        tasks = self.service.list()
        _render_tasks(tasks)
        if not tasks:
            return
        try:
            number = int(input(Fore.CYAN + f"Número da tarefa para {action}: "))
            task = tasks[number - 1] if number > 0 else None
        except (ValueError, IndexError):
            task = None
        if task is None:
            print(Fore.YELLOW + "Número inválido.")
            return
        if action == "concluir":
            self.service.complete(task.id)
            print(Fore.GREEN + "OK: Tarefa concluída!")
        else:
            self.service.remove(task.id)
            print(Fore.GREEN + f"OK: Tarefa '{task.title}' removida!")

    def show_stats(self) -> None:
        stats = self.service.stats()
        print(Fore.MAGENTA + "\nEstatísticas:")
        print(f"- Total: {stats['total']} tarefas\n- Concluídas: {stats['completed']}")
        print(f"- Pendentes: {stats['pending']}\n- Alta: {stats['high']}")
        print(f"- Média: {stats['medium']}\n- Baixa: {stats['low']}")


def build_cli(root: str | Path = ".") -> CLI:
    base = Path(root)
    repository = SQLiteTaskRepository(base / "data" / "eqo.db")
    imported = repository.import_legacy_json(base / "tasks.json")
    if imported:
        print(Fore.GREEN + f"OK: {imported} tarefa(s) importada(s) do formato legado.")
    return CLI(TaskService(repository, base / "backups"))


def main() -> None:
    build_cli().run()
