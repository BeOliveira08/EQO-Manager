from datetime import UTC, datetime

import pytest

from eqo.domain.context import Context
from eqo.domain.state import UserState
from eqo.services.context_engine import ContextEngine


def test_context_uses_clock_state_and_normalizes_empty_activity() -> None:
    instant = datetime(2026, 8, 24, 14, 0, tzinfo=UTC)
    context = ContextEngine(lambda: instant).current(
        UserState(available_minutes=120), current_activity="   "
    )
    assert context.current_time == instant
    assert context.day_of_week == 1
    assert context.available_minutes == 120
    assert context.current_activity is None


def test_context_reflects_day_change() -> None:
    moments = iter([
        datetime(2026, 8, 24, 23, 59, tzinfo=UTC),
        datetime(2026, 8, 25, 0, 1, tzinfo=UTC),
    ])
    engine = ContextEngine(lambda: next(moments))
    assert engine.current(UserState()).day_of_week == 1
    assert engine.current(UserState()).day_of_week == 2


def test_context_requires_timezone_and_nonnegative_availability() -> None:
    with pytest.raises(ValueError, match="fuso"):
        Context(datetime(2026, 8, 24), 10)
    with pytest.raises(ValueError, match="negativo"):
        Context(datetime(2026, 8, 24, tzinfo=UTC), -1)

