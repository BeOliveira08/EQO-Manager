from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Protocol

from eqo.domain.memory import MemoryImportance, MemorySource
from eqo.domain.plan import PlanItemKind
from eqo.domain.state import Capacity, UserState
from eqo.domain.task import Priority, TaskStatus
from eqo.services.context_engine import ContextEngine
from eqo.services.memory_service import MemoryService
from eqo.services.planner import Planner
from eqo.services.profile_service import ProfileService
from eqo.services.state_service import StateService
from eqo.services.task_service import TaskService


@dataclass(frozen=True, slots=True)
class TaskSummary:
    id: str
    title: str
    priority: int
    status: str
    deadline: str | None
    estimated_minutes: int | None


@dataclass(frozen=True, slots=True)
class StateSnapshot:
    capacity: int
    energy: int
    available_minutes: int
    focus: int
    stress: int


@dataclass(frozen=True, slots=True)
class NextAction:
    kind: str
    title: str
    reason: str
    allocated_minutes: int
    task_id: str | None


@dataclass(frozen=True, slots=True)
class DashboardSnapshot:
    schema_version: int
    assistant_name: str
    state: StateSnapshot
    next_action: NextAction | None
    pending_count: int
    capabilities: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class InteractionReply:
    text: str
    requires_confirmation: bool = False


class MobileEQOBackend(Protocol):
    """Fronteira que qualquer shell móvel pode consumir sem conhecer o SQLite."""

    def dashboard(self) -> DashboardSnapshot: ...

    def list_tasks(self, status: TaskStatus | None = None) -> tuple[TaskSummary, ...]: ...

    def add_task(
        self,
        title: str,
        priority: Priority = Priority.MEDIUM,
        deadline: date | None = None,
        *,
        estimated_minutes: int | None = None,
    ) -> TaskSummary: ...

    def complete_task(self, task_id: str) -> TaskSummary: ...

    def update_state(self, state: UserState) -> StateSnapshot: ...

    def remember(self, key: str, value: str) -> None: ...

    def forget(self, key: str) -> bool: ...

    def submit_text(self, text: str) -> InteractionReply: ...

    def request_push_to_talk(self) -> InteractionReply: ...


class ReferenceMobileEQOBackend:
    """Implementação Python de referência; não é uma estratégia de empacotamento Android."""

    SCHEMA_VERSION = 1

    def __init__(
        self,
        tasks: TaskService,
        states: StateService,
        planner: Planner,
        context: ContextEngine,
        profiles: ProfileService,
        memories: MemoryService,
    ) -> None:
        self.tasks = tasks
        self.states = states
        self.planner = planner
        self.context = context
        self.profiles = profiles
        self.memories = memories

    def dashboard(self) -> DashboardSnapshot:
        state = self.states.current()
        pending = self.tasks.list(TaskStatus.PENDING)
        next_action = None
        if state.available_minutes > 0:
            plan = self.planner.create_plan(pending, state, self.context.current(state))
            item = next(
                (candidate for candidate in plan.items if candidate.allocated_minutes),
                None,
            )
            if item is not None:
                next_action = NextAction(
                    kind=item.kind.value,
                    title=item.title,
                    reason=item.reason,
                    allocated_minutes=item.allocated_minutes,
                    task_id=item.task_id if item.kind is PlanItemKind.TASK else None,
                )
        profile = self.profiles.current()
        return DashboardSnapshot(
            schema_version=self.SCHEMA_VERSION,
            assistant_name=profile.assistant_name if profile else "EQO",
            state=self._state(state),
            next_action=next_action,
            pending_count=len(pending),
            capabilities=("tasks", "state", "plan", "memory"),
        )

    def list_tasks(self, status: TaskStatus | None = None) -> tuple[TaskSummary, ...]:
        return tuple(self._task(task) for task in self.tasks.list(status))

    def add_task(
        self,
        title: str,
        priority: Priority = Priority.MEDIUM,
        deadline: date | None = None,
        *,
        estimated_minutes: int | None = None,
    ) -> TaskSummary:
        return self._task(self.tasks.create(
            title, priority, deadline, estimated_minutes=estimated_minutes
        ))

    def complete_task(self, task_id: str) -> TaskSummary:
        return self._task(self.tasks.complete(task_id))

    def update_state(self, state: UserState) -> StateSnapshot:
        updated = self.states.update(
            capacity=state.capacity,
            energy=state.energy,
            available_minutes=state.available_minutes,
            focus=state.focus,
            stress=state.stress,
        )
        return self._state(updated)

    def remember(self, key: str, value: str) -> None:
        self.memories.remember(
            key,
            value,
            importance=MemoryImportance.HIGH,
            source=MemorySource.USER_EXPLICIT,
        )

    def forget(self, key: str) -> bool:
        return self.memories.forget(key)

    def submit_text(self, text: str) -> InteractionReply:
        if not text.strip():
            return InteractionReply("Digite uma mensagem.")
        return InteractionReply(
            "O adapter de conversa não está configurado; use os casos de uso explícitos."
        )

    def request_push_to_talk(self) -> InteractionReply:
        return InteractionReply(
            "O adapter de voz não está configurado; a interface textual continua disponível."
        )

    @staticmethod
    def _task(task: object) -> TaskSummary:
        from eqo.domain.task import Task

        if not isinstance(task, Task):
            raise TypeError("task deve ser Task")
        return TaskSummary(
            id=task.id,
            title=task.title,
            priority=int(task.priority),
            status=task.status.value,
            deadline=task.deadline.isoformat() if task.deadline else None,
            estimated_minutes=task.estimated_minutes,
        )

    @staticmethod
    def _state(state: UserState) -> StateSnapshot:
        return StateSnapshot(
            capacity=int(state.capacity),
            energy=state.energy,
            available_minutes=state.available_minutes,
            focus=state.focus,
            stress=state.stress,
        )


def state_from_values(
    capacity: int, energy: int, available_minutes: int, focus: int, stress: int
) -> UserState:
    """Construtor explícito útil a adapters que recebem apenas tipos primitivos."""
    return UserState(Capacity(capacity), energy, available_minutes, focus, stress)
