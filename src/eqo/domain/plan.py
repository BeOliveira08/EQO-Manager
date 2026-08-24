from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from eqo.domain.decision import Decision


class PlanItemKind(StrEnum):
    TASK = "task"
    REST = "rest"


@dataclass(frozen=True, slots=True)
class PlanItem:
    kind: PlanItemKind
    title: str
    decision: Decision
    reason: str
    allocated_minutes: int
    remaining_minutes: int = 0
    task_id: str | None = None
    starts_at: datetime | None = None
    segments: tuple[int, ...] = ()

    @property
    def deferred(self) -> bool:
        return self.kind is PlanItemKind.TASK and self.allocated_minutes == 0


@dataclass(frozen=True, slots=True)
class Plan:
    created_at: datetime
    available_minutes: int
    items: tuple[PlanItem, ...]

    @property
    def allocated_minutes(self) -> int:
        return sum(item.allocated_minutes for item in self.items)

    @property
    def remaining_capacity(self) -> int:
        return max(0, self.available_minutes - self.allocated_minutes)
