from datetime import date
from pathlib import Path

from eqo.domain.task import Priority
from eqo.services.task_service import TaskService
from eqo.storage.sqlite_repository import SQLiteTaskRepository


def test_crud_search_and_stats(tmp_path: Path) -> None:
    backup_directory = tmp_path / "backups"
    service = TaskService(SQLiteTaskRepository(tmp_path / "eqo.db"), backup_directory)
    first = service.create("Estudar Python", Priority.HIGH, date(2026, 8, 25))
    second = service.create("Responder João", Priority.LOW)
    assert [task.id for task in service.search("python")] == [first.id]
    service.complete(first.id)
    assert len(list(backup_directory.glob("*.db"))) == 2
    assert service.stats() == {
        "total": 2, "completed": 1, "pending": 1,
        "high": 1, "medium": 0, "low": 1,
    }
    service.remove(second.id)
    assert service.stats()["total"] == 1
