import json
from datetime import UTC, datetime

from eqo.application.backup import LogicalBackupService
from eqo.domain.event import Event, EventType
from eqo.domain.memory import Memory
from eqo.domain.state import UserState
from eqo.domain.task import Task
from eqo.domain.user import UserProfile
from eqo.storage.sqlite_event_repository import SQLiteEventRepository
from eqo.storage.sqlite_memory_repository import SQLiteMemoryRepository
from eqo.storage.sqlite_profile_repository import SQLiteUserProfileRepository
from eqo.storage.sqlite_repository import SQLiteTaskRepository
from eqo.storage.sqlite_state_repository import SQLiteUserStateRepository


def test_export_is_versioned_logical_data_not_database_copy(tmp_path) -> None:
    database = tmp_path / "eqo.db"
    tasks = SQLiteTaskRepository(database)
    states = SQLiteUserStateRepository(database)
    profiles = SQLiteUserProfileRepository(database)
    memories = SQLiteMemoryRepository(database)
    events = SQLiteEventRepository(database)
    tasks.add(Task("Exportar meus dados"))
    states.save(UserState())
    profiles.save(UserProfile("Sergio"))
    memories.upsert(Memory("mode", "offline"))
    events.add(Event(EventType.STATE_CHANGED))
    service = LogicalBackupService(tasks, states, profiles, memories, events)
    destination = tmp_path / "export.eqobackup"

    service.export(destination, datetime(2026, 8, 24, tzinfo=UTC))
    raw = destination.read_bytes()
    payload = json.loads(raw)

    assert not raw.startswith(b"SQLite format 3")
    assert payload["format"] == "eqo.logical-backup"
    assert payload["schema_version"] == 1
    assert set(payload["data"]) == {"tasks", "state", "profile", "memories", "events"}
    assert "chat" not in json.dumps(payload).casefold()


def test_logical_backup_requires_explicit_extension(tmp_path) -> None:
    database = tmp_path / "eqo.db"
    service = LogicalBackupService(
        SQLiteTaskRepository(database),
        SQLiteUserStateRepository(database),
        SQLiteUserProfileRepository(database),
        SQLiteMemoryRepository(database),
        SQLiteEventRepository(database),
    )

    try:
        service.export(tmp_path / "unsafe.db")
    except ValueError as error:
        assert ".eqobackup" in str(error)
    else:
        raise AssertionError("A extensão inválida deveria ter sido rejeitada")
