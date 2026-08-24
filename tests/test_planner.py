from datetime import UTC, date, datetime

from eqo.domain.context import Context
from eqo.domain.decision import Decision
from eqo.domain.plan import PlanItemKind
from eqo.domain.state import Capacity, UserState
from eqo.domain.task import Priority, Task
from eqo.services.planner import Planner

NOW = datetime(2026, 8, 24, 14, 0, tzinfo=UTC)


def test_adaptive_plan_prioritizes_urgent_reduces_and_defers() -> None:
    tasks = [
        Task(
            title="Estudar Python", priority=Priority.HIGH,
            estimated_minutes=120, effort=5, flexibility=5,
        ),
        Task(
            title="Limpar quarto", estimated_minutes=60,
            effort=4, flexibility=1,
        ),
        Task(
            title="Pagar conta", priority=Priority.HIGH,
            deadline=date(2026, 8, 24), estimated_minutes=10,
            effort=1, flexibility=1,
        ),
    ]
    plan = Planner().create_plan(
        tasks,
        UserState(capacity=Capacity.LOW, energy=2, available_minutes=120),
        Context(NOW, available_minutes=120),
    )
    task_items = [item for item in plan.items if item.kind is PlanItemKind.TASK]
    assert task_items[0].title == "Pagar conta"
    assert task_items[0].decision is Decision.EXECUTE
    by_title = {item.title: item for item in task_items}
    assert by_title["Limpar quarto"].decision is Decision.REDUCE
    assert by_title["Limpar quarto"].allocated_minutes == 20
    assert by_title["Estudar Python"].decision is Decision.DEFER
    assert by_title["Estudar Python"].remaining_minutes == 120
    assert plan.allocated_minutes == 30


def test_plan_splits_task_into_concrete_segments_when_time_is_short() -> None:
    task = Task(
        title="Estudo", estimated_minutes=100,
        effort=3, flexibility=3,
    )
    plan = Planner().create_plan(
        [task], UserState(capacity=Capacity.HIGH), Context(NOW, 45)
    )
    item = plan.items[0]
    assert item.decision is Decision.SPLIT
    assert item.segments == (30, 15)
    assert item.allocated_minutes == 45
    assert item.remaining_minutes == 55


def test_plan_detects_capacity_conflict_and_defers_later_task() -> None:
    first = Task(title="Primeira", estimated_minutes=30, priority=Priority.HIGH)
    second = Task(title="Segunda", estimated_minutes=30, priority=Priority.LOW)
    plan = Planner().create_plan(
        [second, first], UserState(capacity=Capacity.HIGH), Context(NOW, 30)
    )
    assert plan.items[0].task_id == first.id
    assert plan.items[1].decision is Decision.DEFER
    assert plan.items[1].allocated_minutes == 0


def test_plan_recommends_one_rest_without_mutating_tasks() -> None:
    task = Task(title="Organizar", estimated_minutes=60, flexibility=5)
    plan = Planner().create_plan(
        [task],
        UserState(capacity=Capacity.VERY_LOW, energy=1, stress=5),
        Context(NOW, 60),
    )
    assert plan.items[0].kind is PlanItemKind.REST
    assert plan.items[0].allocated_minutes == 30
    assert plan.items[1].decision is Decision.DEFER
    assert task.completed is False
    assert task.estimated_minutes == 60
