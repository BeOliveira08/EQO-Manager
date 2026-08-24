import json
from pathlib import Path

from eqo.domain.task import Priority, Task, TaskStatus
from eqo.storage.sqlite_repository import SQLiteTaskRepository


def test_imports_legacy_json_once(tmp_path: Path) -> None:
    legacy = tmp_path / "tasks.json"
    legacy.write_text(json.dumps([
        {"title": "Pagar conta", "completed": False, "priority": "1", "deadline": "2026-08-25"},
        {"title": "Arquivar", "completed": True, "priority": "3", "deadline": None},
    ]), encoding="utf-8")
    repository = SQLiteTaskRepository(tmp_path / "data" / "eqo.db")
    assert repository.import_legacy_json(legacy) == 2
    assert repository.import_legacy_json(legacy) == 0
    assert repository.list()[0].priority is Priority.HIGH
    assert repository.list(TaskStatus.COMPLETED)[0].title == "Arquivar"


def test_invalid_legacy_json_is_ignored(tmp_path: Path) -> None:
    legacy = tmp_path / "tasks.json"
    legacy.write_text("{inválido", encoding="utf-8")
    repository = SQLiteTaskRepository(tmp_path / "eqo.db")
    assert repository.import_legacy_json(legacy) == 0


def test_order_and_filters_are_stable(tmp_path: Path) -> None:
    repository = SQLiteTaskRepository(tmp_path / "eqo.db")
    low = Task(title="Baixa", priority=Priority.LOW)
    high = Task(title="Alta", priority=Priority.HIGH)
    low.complete()
    repository.add(low)
    repository.add(high)
    assert [task.title for task in repository.list()] == ["Alta", "Baixa"]
    assert [task.title for task in repository.list(TaskStatus.PENDING)] == ["Alta"]
    assert [task.title for task in repository.list(TaskStatus.COMPLETED)] == ["Baixa"]
