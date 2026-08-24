from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4


class EventType(StrEnum):
    TASK_COMPLETED = "task_completed"
    STATE_CHANGED = "state_changed"
    PREFERENCE_CHANGED = "preference_changed"
    STUDY_SESSION = "study_session"
    MEMORY_CREATED = "memory_created"
    MEMORY_FORGOTTEN = "memory_forgotten"
    PLAN_ACCEPTED = "plan_accepted"
    PLAN_REJECTED = "plan_rejected"


@dataclass(frozen=True, slots=True)
class Event:
    event_type: EventType
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    attributes: tuple[tuple[str, str], ...] = ()
    id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if self.occurred_at.tzinfo is None:
            raise ValueError("A data do evento deve possuir fuso horário.")
        keys = [key for key, _ in self.attributes]
        if len(keys) != len(set(keys)):
            raise ValueError("Atributos de evento não podem repetir chaves.")

    def attribute(self, key: str) -> str | None:
        return dict(self.attributes).get(key)
