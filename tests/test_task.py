from datetime import UTC, datetime

import pytest

from eqo.domain.task import Task, TaskStatus


def test_task_rejects_empty_title() -> None:
    with pytest.raises(ValueError, match="título"):
        Task(title="   ")


def test_complete_records_state_and_time() -> None:
    task = Task(title="Estudar")
    when = datetime(2026, 8, 24, tzinfo=UTC)
    task.complete(when)
    assert task.status is TaskStatus.COMPLETED
    assert task.completed_at == when
