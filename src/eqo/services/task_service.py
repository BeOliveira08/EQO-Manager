from __future__ import annotations

import builtins
from datetime import date
from pathlib import Path

from eqo.domain.task import Priority, Task, TaskStatus
from eqo.storage.repositories import BackupRepository, TaskRepository


class TaskService:
    def __init__(self, repository: TaskRepository,
                 backup_directory: str | Path | None = None) -> None:
        self.repository = repository
        self.backup_directory = backup_directory

    def create(self, title: str, priority: Priority = Priority.MEDIUM,
               deadline: date | None = None, *,
               estimated_minutes: int | None = None,
               effort: int = 3, flexibility: int = 3) -> Task:
        task = Task(
            title=title,
            priority=priority,
            deadline=deadline,
            estimated_minutes=estimated_minutes,
            effort=effort,
            flexibility=flexibility,
        )
        self._backup()
        self.repository.add(task)
        return task

    def list(self, status: TaskStatus | None = None) -> list[Task]:
        return self.repository.list(status)

    def search(self, term: str) -> builtins.list[Task]:
        normalized = term.casefold().strip()
        return [task for task in self.list() if normalized in task.title.casefold()]

    def complete(self, task_id: str) -> Task:
        task = self._required(task_id)
        self._backup()
        task.complete()
        self.repository.save(task)
        return task

    def remove(self, task_id: str) -> Task:
        task = self._required(task_id)
        self._backup()
        self.repository.remove(task_id)
        return task

    def stats(self) -> dict[str, int]:
        tasks = self.list()
        return {
            "total": len(tasks),
            "completed": sum(task.completed for task in tasks),
            "pending": sum(not task.completed for task in tasks),
            "high": sum(task.priority is Priority.HIGH for task in tasks),
            "medium": sum(task.priority is Priority.MEDIUM for task in tasks),
            "low": sum(task.priority is Priority.LOW for task in tasks),
        }

    def _required(self, task_id: str) -> Task:
        task = self.repository.get(task_id)
        if task is None:
            raise LookupError(f"Tarefa não encontrada: {task_id}")
        return task

    def _backup(self) -> None:
        if (
            self.backup_directory is not None
            and isinstance(self.repository, BackupRepository)
        ):
            self.repository.backup_to(self.backup_directory)
