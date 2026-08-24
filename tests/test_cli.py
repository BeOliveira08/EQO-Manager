from datetime import date
from pathlib import Path

from eqo.cli.interface import CLI, _render_tasks
from eqo.domain.task import Priority, Task, TaskStatus
from eqo.services.task_service import TaskService
from eqo.storage.sqlite_repository import SQLiteTaskRepository


def test_complete_cli_workflow_preserves_displayed_order(
    tmp_path: Path, monkeypatch: object, capsys: object
) -> None:
    repository = SQLiteTaskRepository(tmp_path / "eqo.db")
    service = TaskService(repository, tmp_path / "backups")
    answers = iter([
        "1", "Baixa", "3", "n",
        "1", "Urgente", "1", "n",
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
