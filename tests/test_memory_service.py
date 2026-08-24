import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from eqo.domain.memory import MemoryImportance, MemorySource, MemoryType
from eqo.services.memory_service import MemoryService, WorkingMemory
from eqo.storage.sqlite_event_repository import SQLiteEventRepository
from eqo.storage.sqlite_memory_repository import SQLiteMemoryRepository


def make_service(tmp_path: Path) -> tuple[MemoryService, Path]:
    database = tmp_path / "eqo.db"
    return MemoryService(
        SQLiteMemoryRepository(database), SQLiteEventRepository(database)
    ), database


def test_memory_create_update_restart_and_structured_metadata(tmp_path: Path) -> None:
    service, database = make_service(tmp_path)
    first = service.remember(
        "preferred_study_time",
        "evening",
        importance=MemoryImportance.HIGH,
        confidence=1.0,
        source=MemorySource.USER_PREFERENCE,
    )
    updated = service.remember(
        "preferred_study_time",
        "night",
        importance=MemoryImportance.HIGH,
        confidence=0.9,
        source=MemorySource.USER_EXPLICIT,
    )
    restored = MemoryService(SQLiteMemoryRepository(database)).recall(
        "preferred_study_time"
    )
    assert updated.id == first.id
    assert restored is not None
    assert restored.value == "night"
    assert restored.importance is MemoryImportance.HIGH
    assert restored.confidence == 0.9
    assert restored.source is MemorySource.USER_EXPLICIT


def test_expired_memory_is_hidden_then_physically_purged(tmp_path: Path) -> None:
    service, database = make_service(tmp_path)
    service.remember(
        "temporary_state",
        "cansado hoje",
        memory_type=MemoryType.EPISODIC,
        expires_at=datetime.now(UTC) - timedelta(minutes=1),
    )
    assert service.recall("temporary_state", MemoryType.EPISODIC) is None
    assert service.purge_expired() == 1
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM memories").fetchone()[0] == 0


def test_forget_physically_removes_memory_and_search_index(tmp_path: Path) -> None:
    service, database = make_service(tmp_path)
    service.remember("study_preference", "prefere estudar à noite")
    assert service.search("estudar noite")
    assert service.forget("study_preference") is True
    assert service.recall("study_preference") is None
    assert service.search("estudar noite") == []
    assert service.forget("study_preference") is False
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM memories").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM memory_fts").fetchone()[0] == 0


def test_memory_validation_rejects_invalid_confidence(tmp_path: Path) -> None:
    service, _ = make_service(tmp_path)
    with pytest.raises(ValueError, match="confiança"):
        service.remember("key", "value", confidence=1.1)


def test_working_memory_is_bounded_and_session_only() -> None:
    working = WorkingMemory(capacity=2)
    working.set("topic", "Python")
    working.set("detail", "testing")
    working.set("next", "SQLite")
    assert working.get("topic") is None
    assert working.items() == (("detail", "testing"), ("next", "SQLite"))
    working.clear()
    assert working.items() == ()

