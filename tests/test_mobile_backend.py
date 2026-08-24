from datetime import UTC, datetime
from pathlib import Path

from eqo.application.mobile_backend import ReferenceMobileEQOBackend
from eqo.domain.state import Capacity, UserState
from eqo.domain.task import Priority
from eqo.services.context_engine import ContextEngine
from eqo.services.memory_service import MemoryService
from eqo.services.planner import Planner
from eqo.services.profile_service import ProfileService
from eqo.services.state_service import StateService
from eqo.services.task_service import TaskService
from eqo.storage.sqlite_event_repository import SQLiteEventRepository
from eqo.storage.sqlite_memory_repository import SQLiteMemoryRepository
from eqo.storage.sqlite_profile_repository import SQLiteUserProfileRepository
from eqo.storage.sqlite_repository import SQLiteTaskRepository
from eqo.storage.sqlite_state_repository import SQLiteUserStateRepository


def build_backend(tmp_path: Path) -> ReferenceMobileEQOBackend:
    database = tmp_path / "eqo.db"
    return ReferenceMobileEQOBackend(
        TaskService(SQLiteTaskRepository(database)),
        StateService(SQLiteUserStateRepository(database)),
        Planner(),
        ContextEngine(lambda: datetime(2026, 8, 24, 12, tzinfo=UTC)),
        ProfileService(SQLiteUserProfileRepository(database)),
        MemoryService(SQLiteMemoryRepository(database), SQLiteEventRepository(database)),
    )


def test_dashboard_prioritizes_one_next_action_offline(tmp_path: Path) -> None:
    backend = build_backend(tmp_path)
    backend.add_task("Preparar revisão", Priority.HIGH, estimated_minutes=30)
    backend.add_task("Organizar referências", Priority.LOW, estimated_minutes=30)
    backend.update_state(UserState(Capacity.HIGH, 4, 45, 4, 2))

    dashboard = backend.dashboard()

    assert dashboard.schema_version == 1
    assert dashboard.pending_count == 2
    assert dashboard.next_action is not None
    assert dashboard.next_action.title == "Preparar revisão"
    assert dashboard.next_action.allocated_minutes == 30
    assert dashboard.to_dict()["assistant_name"] == "EQO"


def test_mobile_backend_task_and_memory_flow(tmp_path: Path) -> None:
    backend = build_backend(tmp_path)
    task = backend.add_task("Fluxo no modo avião")
    backend.remember("preferred_mode", "offline")

    completed = backend.complete_task(task.id)

    assert completed.status == "completed"
    assert len(backend.list_tasks()) == 1
    assert backend.forget("preferred_mode") is True
