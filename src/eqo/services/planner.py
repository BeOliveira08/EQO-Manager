from datetime import datetime, timedelta

from eqo.domain.context import Context
from eqo.domain.decision import Decision, DecisionResult
from eqo.domain.plan import Plan, PlanItem, PlanItemKind
from eqo.domain.state import UserState
from eqo.domain.task import Task
from eqo.services.decision_engine import DecisionEngine


class Planner:
    """Produz recomendações; nunca persiste ou modifica tarefas."""

    DEFAULT_DURATION = 30
    REDUCED_DURATION = 20
    REST_DURATION = 30
    SEGMENT_DURATION = 30

    def __init__(self, decision_engine: DecisionEngine | None = None) -> None:
        self.decision_engine = decision_engine or DecisionEngine()

    def create_plan(
        self, tasks: list[Task], state: UserState, context: Context
    ) -> Plan:
        ordered = sorted(
            (task for task in tasks if not task.completed),
            key=self._sort_key,
        )
        remaining = context.available_minutes
        cursor = context.current_time
        items: list[PlanItem] = []
        rest_added = False

        for task in ordered:
            result = self.decision_engine.evaluate(task, state, context.current_time.date())
            if result.decision is Decision.REST:
                if not rest_added and remaining > 0:
                    duration = min(self.REST_DURATION, remaining)
                    items.append(PlanItem(
                        kind=PlanItemKind.REST,
                        title="Descanso",
                        decision=Decision.REST,
                        reason=result.reason,
                        allocated_minutes=duration,
                        starts_at=cursor,
                    ))
                    cursor += timedelta(minutes=duration)
                    remaining -= duration
                    rest_added = True
                result = self._after_rest(task)

            item = self._plan_task(task, result, remaining, cursor)
            items.append(item)
            remaining -= item.allocated_minutes
            cursor += timedelta(minutes=item.allocated_minutes)

        return Plan(
            created_at=context.current_time,
            available_minutes=context.available_minutes,
            items=tuple(items),
        )

    def _plan_task(
        self,
        task: Task,
        result: DecisionResult,
        remaining: int,
        starts_at: datetime,
    ) -> PlanItem:
        duration = task.estimated_minutes or self.DEFAULT_DURATION
        if result.decision is Decision.DEFER or remaining == 0:
            return self._task_item(task, Decision.DEFER, result.reason, 0, duration, starts_at)
        if result.decision is Decision.REDUCE:
            allocated = min(duration, self.REDUCED_DURATION, remaining)
            return self._task_item(
                task, Decision.REDUCE, result.reason, allocated,
                duration - allocated, starts_at,
            )
        if result.decision is Decision.SPLIT or duration > remaining:
            allocated = min(duration, remaining)
            segments = self._segments(allocated)
            reason = (
                result.reason
                if result.decision is Decision.SPLIT
                else "A tarefa excede o tempo restante do contexto atual."
            )
            return self._task_item(
                task, Decision.SPLIT, reason, allocated,
                duration - allocated, starts_at, segments,
            )
        return self._task_item(
            task, result.decision, result.reason, duration, 0, starts_at
        )

    @staticmethod
    def _after_rest(task: Task) -> DecisionResult:
        if task.flexibility >= 4:
            return DecisionResult(Decision.DEFER, "Tarefa flexível após recomendação de descanso.")
        return DecisionResult(Decision.REDUCE, "Escopo reduzido após recomendação de descanso.")

    @classmethod
    def _segments(cls, duration: int) -> tuple[int, ...]:
        complete, remainder = divmod(duration, cls.SEGMENT_DURATION)
        segments = (cls.SEGMENT_DURATION,) * complete
        return segments + ((remainder,) if remainder else ())

    @staticmethod
    def _sort_key(task: Task) -> tuple[object, ...]:
        return (
            task.deadline is None,
            task.deadline,
            int(task.priority),
            task.flexibility,
            task.created_at,
        )

    @staticmethod
    def _task_item(
        task: Task,
        decision: Decision,
        reason: str,
        allocated: int,
        remaining: int,
        starts_at: datetime,
        segments: tuple[int, ...] = (),
    ) -> PlanItem:
        return PlanItem(
            kind=PlanItemKind.TASK,
            task_id=task.id,
            title=task.title,
            decision=decision,
            reason=reason,
            allocated_minutes=allocated,
            remaining_minutes=remaining,
            starts_at=starts_at if allocated else None,
            segments=segments,
        )
