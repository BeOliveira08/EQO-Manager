from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class ScheduledReminder:
    id: str
    task_id: str
    title: str
    trigger_at: datetime

    def __post_init__(self) -> None:
        if self.trigger_at.tzinfo is None:
            raise ValueError("O agendamento deve possuir fuso horário.")


class Scheduler(Protocol):
    def schedule(self, task_id: str, title: str, trigger_at: datetime) -> ScheduledReminder: ...

    def cancel(self, reminder_id: str) -> bool: ...

    def due(self, now: datetime) -> tuple[ScheduledReminder, ...]: ...


class LocalScheduler:
    """Referência determinística; não executa nem conclui tarefas autonomamente."""

    def __init__(self) -> None:
        self._reminders: dict[str, ScheduledReminder] = {}

    def schedule(self, task_id: str, title: str, trigger_at: datetime) -> ScheduledReminder:
        reminder = ScheduledReminder(str(uuid4()), task_id, title.strip(), trigger_at)
        if not reminder.title:
            raise ValueError("O título do lembrete é obrigatório.")
        self._reminders[reminder.id] = reminder
        return reminder

    def cancel(self, reminder_id: str) -> bool:
        return self._reminders.pop(reminder_id, None) is not None

    def due(self, now: datetime) -> tuple[ScheduledReminder, ...]:
        if now.tzinfo is None:
            raise ValueError("A consulta deve possuir fuso horário.")
        return tuple(sorted(
            (item for item in self._reminders.values() if item.trigger_at <= now),
            key=lambda item: (item.trigger_at, item.id),
        ))
