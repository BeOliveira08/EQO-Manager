from datetime import UTC, date, datetime
from pathlib import Path

from eqo.cli.interface import CLI, _render_tasks
from eqo.domain.task import Priority, Task, TaskStatus
from eqo.services.context_engine import ContextEngine
from eqo.services.planner import Planner
from eqo.services.state_service import StateService
from eqo.services.task_service import TaskService
from eqo.storage.sqlite_repository import SQLiteTaskRepository
from eqo.storage.sqlite_state_repository import SQLiteUserStateRepository


def test_complete_cli_workflow_preserves_displayed_order(
    tmp_path: Path, monkeypatch: object, capsys: object
) -> None:
    repository = SQLiteTaskRepository(tmp_path / "eqo.db")
    service = TaskService(repository, tmp_path / "backups")
    answers = iter([
        "1", "Baixa", "3", "n", "", "", "",
        "1", "Urgente", "1", "n", "", "", "",
        "2",
        "5", "baixa",
        "4",
        "6", "1",
        "3",
        "7", "2",
        "9",
    ])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))  # type: ignore[attr-defined]

    CLI(service).run()

    remaining = service.list()
    assert len(remaining) == 1
    assert remaining[0].title == "Urgente"
    assert remaining[0].status is TaskStatus.COMPLETED
    output = capsys.readouterr().out  # type: ignore[attr-defined]
    assert "Tarefa adicionada" in output
    assert "Baixa" in output
    assert "Tarefa concluída" in output
    assert "Tarefa 'Baixa' removida" in output


def test_render_deadline_states(capsys: object) -> None:
    tasks = [
        Task(title="Atrasada", priority=Priority.HIGH, deadline=date(2026, 8, 23)),
        Task(title="Hoje", deadline=date(2026, 8, 24)),
        Task(title="Futura", deadline=date(2026, 8, 26)),
    ]
    _render_tasks(tasks, today=date(2026, 8, 24))
    output = capsys.readouterr().out  # type: ignore[attr-defined]
    assert "[ATRASADA]" in output
    assert "[HOJE]" in output
    assert "2d" in output


def test_cli_updates_state_and_displays_non_mutating_plan(
    tmp_path: Path, monkeypatch: object, capsys: object
) -> None:
    database = tmp_path / "eqo.db"
    task_service = TaskService(SQLiteTaskRepository(database))
    task = task_service.create(
        "Pagar conta",
        Priority.HIGH,
        date(2026, 8, 24),
        estimated_minutes=10,
        effort=1,
        flexibility=1,
    )
    state_service = StateService(SQLiteUserStateRepository(database))
    cli = CLI(
        task_service,
        state_service,
        Planner(),
        ContextEngine(lambda: datetime(2026, 8, 24, 14, 0, tzinfo=UTC)),
    )
    answers = iter(["10", "2", "2", "120", "2", "3", "11", "9"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))  # type: ignore[attr-defined]

    cli.run()

    output = capsys.readouterr().out  # type: ignore[attr-defined]
    assert "Estado atualizado" in output
    assert "Plano sugerido" in output
    assert "Pagar conta [execute]" in output
    assert task_service.list()[0].completed is False
    assert task_service.list()[0].id == task.id
