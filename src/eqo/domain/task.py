from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from enum import IntEnum, StrEnum
from uuid import uuid4


class Priority(IntEnum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3

    @property
    def label(self) -> str:
        return {self.HIGH: "Alta", self.MEDIUM: "Média", self.LOW: "Baixa"}[self]


class TaskStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"


@dataclass(slots=True)
class Task:
    title: str
    priority: Priority = Priority.MEDIUM
    deadline: date | None = None
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    estimated_minutes: int | None = None
    effort: int = 3
    flexibility: int = 3
    context: str | None = None
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        self.title = self.title.strip()
        if not self.title:
            raise ValueError("O título não pode estar vazio.")
        if not 1 <= self.effort <= 5 or not 1 <= self.flexibility <= 5:
            raise ValueError("Esforço e flexibilidade devem estar entre 1 e 5.")
        if self.estimated_minutes is not None and self.estimated_minutes <= 0:
            raise ValueError("A duração estimada deve ser positiva.")

    @property
    def completed(self) -> bool:
        return self.status is TaskStatus.COMPLETED

    def complete(self, when: datetime | None = None) -> None:
        self.status = TaskStatus.COMPLETED
        self.completed_at = when or datetime.now(UTC)
