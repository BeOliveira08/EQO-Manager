from datetime import UTC, datetime, timedelta

from eqo.application.scheduler import LocalScheduler


def test_scheduler_is_deterministic_and_does_not_mutate_tasks() -> None:
    scheduler = LocalScheduler()
    now = datetime(2026, 8, 24, 12, tzinfo=UTC)
    later = scheduler.schedule("task-2", "Depois", now + timedelta(minutes=30))
    first = scheduler.schedule("task-1", "Agora", now)

    assert scheduler.due(now) == (first,)
    assert scheduler.due(now + timedelta(hours=1)) == (first, later)
    assert scheduler.cancel(first.id) is True
    assert scheduler.cancel(first.id) is False
