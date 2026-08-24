from pathlib import Path
from typing import Protocol, runtime_checkable

from eqo.domain.state import UserState
from eqo.domain.task import Task, TaskStatus


class TaskRepository(Protocol):
    """Porta de persistência usada pelo serviço de tarefas."""

    def add(self, task: Task) -> None: ...

    def save(self, task: Task) -> None: ...

    def get(self, task_id: str) -> Task | None: ...

    def list(self, status: TaskStatus | None = None) -> list[Task]: ...

    def remove(self, task_id: str) -> bool: ...


@runtime_checkable
class BackupRepository(Protocol):
    def backup_to(self, directory: str | Path) -> Path | None: ...


class UserStateRepository(Protocol):
    def get(self) -> UserState | None: ...

    def save(self, state: UserState) -> None: ...

