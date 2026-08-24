from datetime import date

from eqo.domain.state import Capacity, UserState
from eqo.domain.task import Task
from eqo.services.decision_engine import Decision, DecisionEngine


def test_low_capacity_defers_high_effort() -> None:
    result = DecisionEngine().recommend(
        Task(title="Trabalho pesado", effort=5, flexibility=5),
        UserState(capacity=Capacity.LOW),
    )
    assert result is Decision.DEFER


def test_low_capacity_executes_light_effort() -> None:
    result = DecisionEngine().recommend(
        Task(title="Beber água", effort=1, flexibility=1),
        UserState(capacity=Capacity.LOW),
    )
    assert result is Decision.EXECUTE


def test_overdue_task_is_executed_even_with_low_capacity() -> None:
    result = DecisionEngine().evaluate(
        Task(title="Conta", effort=5, deadline=date(2026, 8, 23)),
        UserState(capacity=Capacity.VERY_LOW, stress=5),
        today=date(2026, 8, 24),
    )
    assert result.decision is Decision.EXECUTE
    assert "prazo" in result.reason.casefold()


def test_task_larger_than_available_time_is_split() -> None:
    result = DecisionEngine().evaluate(
        Task(title="Relatório", estimated_minutes=60),
        UserState(available_minutes=20),
    )
    assert result.decision is Decision.SPLIT


def test_very_low_capacity_and_high_stress_recommends_rest() -> None:
    result = DecisionEngine().evaluate(
        Task(title="Organizar mesa"),
        UserState(capacity=Capacity.VERY_LOW, stress=5),
    )
    assert result.decision is Decision.REST
