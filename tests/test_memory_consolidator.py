from datetime import UTC, datetime
from pathlib import Path

from eqo.domain.event import Event, EventType
from eqo.domain.memory import MemorySource
from eqo.services.memory_consolidator import MemoryConsolidator
from eqo.services.memory_service import MemoryService
from eqo.storage.sqlite_event_repository import SQLiteEventRepository
from eqo.storage.sqlite_memory_repository import SQLiteMemoryRepository


def study_event(day: int, hour: int) -> Event:
    return Event(
        EventType.STUDY_SESSION,
        datetime(2026, 8, day, hour, tzinfo=UTC),
        (("hour", str(hour)),),
    )


def test_events_consolidate_into_one_semantic_pattern_without_duplicates(
    tmp_path: Path,
) -> None:
    database = tmp_path / "eqo.db"
    events = SQLiteEventRepository(database)
    memories = SQLiteMemoryRepository(database)
    for event in [
        study_event(20, 20), study_event(21, 19),
        study_event(22, 20), study_event(23, 10),
    ]:
        events.add(event)
    consolidator = MemoryConsolidator(memories, events)
    first = consolidator.consolidate_study_time()
    second = consolidator.consolidate_study_time()
    assert first is not None
    assert second is not None
    assert first.id == second.id
    assert first.value == "evening"
    assert first.confidence == 0.75
    assert first.source is MemorySource.INFERRED
    assert len(memories.list_memories()) == 1


def test_consolidation_requires_enough_consistent_evidence(tmp_path: Path) -> None:
    database = tmp_path / "eqo.db"
    events = SQLiteEventRepository(database)
    memories = SQLiteMemoryRepository(database)
    events.add(study_event(20, 20))
    events.add(study_event(21, 10))
    assert MemoryConsolidator(memories, events).consolidate_study_time() is None
    assert memories.list_memories() == []


def test_forgetting_inferred_pattern_prevents_recreation(tmp_path: Path) -> None:
    database = tmp_path / "eqo.db"
    events = SQLiteEventRepository(database)
    memories = SQLiteMemoryRepository(database)
    for event in [study_event(20, 20), study_event(21, 19), study_event(22, 20)]:
        events.add(event)
    consolidator = MemoryConsolidator(memories, events)
    assert consolidator.consolidate_study_time() is not None
    assert MemoryService(memories, events).forget("preferred_study_time") is True
    assert consolidator.consolidate_study_time() is None
    assert memories.list_memories() == []
