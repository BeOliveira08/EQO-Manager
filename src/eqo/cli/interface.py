from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from colorama import Fore, init  # type: ignore[import-untyped]

from eqo.domain.plan import Plan
from eqo.domain.state import Capacity
from eqo.domain.task import Priority, Task, TaskStatus
from eqo.services.context_engine import ContextEngine
from eqo.services.planner import Planner
from eqo.services.state_service import StateService
from eqo.services.task_service import TaskService
from eqo.storage.sqlite_repository import SQLiteTaskRepository
from eqo.storage.sqlite_state_repository import SQLiteUserStateRepository

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
    def __init__(
        self,
        service: TaskService,
        state_service: StateService | None = None,
        planner: Planner | None = None,
        context_engine: ContextEngine | None = None,
    ) -> None:
        self.service = service
        self.state_service = state_service
        self.planner = planner
        self.context_engine = context_engine

    def run(self) -> None:
        while True:
            print(Fore.BLUE + "\n--- EQO ---")
            print("1. Adicionar tarefa\n2. Listar todas\n3. Listar concluídas")
            print("4. Listar pendentes\n5. Buscar tarefas\n6. Concluir tarefa")
            print("7. Remover tarefa\n8. Estatísticas\n9. Sair")
            if self.state_service is not None:
                print("10. Atualizar meu estado\n11. Sugerir plano")
            choice = input(Fore.CYAN + "Escolha: ").strip()
            actions = {
                "1": self.add_task, "2": lambda: self.list_tasks(),
                "3": lambda: self.list_tasks(TaskStatus.COMPLETED),
                "4": lambda: self.list_tasks(TaskStatus.PENDING), "5": self.search_tasks,
                "6": lambda: self.manage_task("concluir"),
                "7": lambda: self.manage_task("remover"), "8": self.show_stats,
                "10": self.update_state,
                "11": self.show_plan,
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
        try:
            raw_duration = input("Duração estimada em minutos (opcional): ").strip()
            estimated_minutes = int(raw_duration) if raw_duration else None
            effort = int(input("Esforço de 1 a 5 [3]: ").strip() or "3")
            flexibility = int(input("Flexibilidade de 1 a 5 [3]: ").strip() or "3")
            self.service.create(
                title,
                priority,
                deadline,
                estimated_minutes=estimated_minutes,
                effort=effort,
                flexibility=flexibility,
            )
        except ValueError as error:
            print(Fore.RED + f"Dados de demanda inválidos: {error}")
            return
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

    def update_state(self) -> None:
        if self.state_service is None:
            print(Fore.YELLOW + "Estado do usuário indisponível.")
            return
        try:
            state = self.state_service.update(
                capacity=Capacity(int(input("Capacidade de 1 a 5: ").strip())),
                energy=int(input("Energia de 1 a 5: ").strip()),
                available_minutes=int(input("Minutos disponíveis: ").strip()),
                focus=int(input("Foco de 1 a 5: ").strip()),
                stress=int(input("Estresse de 1 a 5: ").strip()),
            )
        except ValueError as error:
            print(Fore.RED + f"Estado inválido: {error}")
            return
        print(Fore.GREEN + f"OK: Estado atualizado; {state.available_minutes} min disponíveis.")

    def show_plan(self) -> None:
        if self.state_service is None or self.planner is None or self.context_engine is None:
            print(Fore.YELLOW + "Planejamento indisponível.")
            return
        state = self.state_service.current()
        context = self.context_engine.current(state)
        if context.available_minutes == 0:
            print(Fore.YELLOW + "Informe seu tempo disponível antes de planejar.")
            return
        plan = self.planner.create_plan(self.service.list(), state, context)
        self._render_plan(plan)

    @staticmethod
    def _render_plan(plan: Plan) -> None:
        print(Fore.BLUE + "\nPlano sugerido (nenhuma tarefa foi alterada):")
        for item in plan.items:
            if item.allocated_minutes:
                start = item.starts_at.strftime("%H:%M") if item.starts_at else "--:--"
                segments = f" segmentos={item.segments}" if item.segments else ""
                print(
                    f"- {start} | {item.allocated_minutes} min | {item.title} "
                    f"[{item.decision.value}]{segments}"
                )
            else:
                print(f"- Depois | {item.title} [{item.decision.value}]")
            print(f"  Motivo: {item.reason}")
        print(f"Tempo ainda livre: {plan.remaining_capacity} min")


def build_cli(root: str | Path = ".") -> CLI:
    base = Path(root)
    repository = SQLiteTaskRepository(base / "data" / "eqo.db")
    state_repository = SQLiteUserStateRepository(base / "data" / "eqo.db")
    imported = repository.import_legacy_json(base / "tasks.json")
    if imported:
        print(Fore.GREEN + f"OK: {imported} tarefa(s) importada(s) do formato legado.")
    return CLI(
        TaskService(repository, base / "backups"),
        StateService(state_repository),
        Planner(),
        ContextEngine(),
    )


def main() -> None:
    build_cli().run()
