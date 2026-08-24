import builtins
from collections import OrderedDict
from datetime import datetime

from eqo.domain.event import Event, EventType
from eqo.domain.memory import (
    Memory,
    MemoryImportance,
    MemorySource,
    MemoryType,
)
from eqo.storage.repositories import EventRepository, MemoryRepository


class WorkingMemory:
    """Contexto limitado à sessão; nunca é enviado ao repositório persistente."""

    def __init__(self, capacity: int = 20) -> None:
        if capacity <= 0:
            raise ValueError("A capacidade da memória de trabalho deve ser positiva.")
        self.capacity = capacity
        self._items: OrderedDict[str, str] = OrderedDict()

    def set(self, key: str, value: str) -> None:
        if not key.strip() or not value.strip():
            raise ValueError("Chave e valor são obrigatórios.")
        self._items.pop(key, None)
        self._items[key] = value
        if len(self._items) > self.capacity:
            self._items.popitem(last=False)

    def get(self, key: str) -> str | None:
        return self._items.get(key)

    def clear(self) -> None:
        self._items.clear()

    def items(self) -> tuple[tuple[str, str], ...]:
        return tuple(self._items.items())


class MemoryService:
    INFERENCE_EVIDENCE = {
        "preferred_study_time": EventType.STUDY_SESSION,
    }

    def __init__(
        self,
        repository: MemoryRepository,
        events: EventRepository | None = None,
    ) -> None:
        self.repository = repository
        self.events = events
        self.working = WorkingMemory()

    def remember(
        self,
        key: str,
        value: str,
        *,
        memory_type: MemoryType = MemoryType.SEMANTIC,
        importance: MemoryImportance = MemoryImportance.MEDIUM,
        confidence: float = 1.0,
        source: MemorySource = MemorySource.USER_EXPLICIT,
        expires_at: datetime | None = None,
    ) -> Memory:
        memory = self.repository.upsert(Memory(
            key=key,
            value=value,
            memory_type=memory_type,
            importance=importance,
            confidence=confidence,
            source=source,
            expires_at=expires_at,
        ))
        self._record(EventType.MEMORY_CREATED)
        return memory

    def recall(
        self, key: str, memory_type: MemoryType = MemoryType.SEMANTIC
    ) -> Memory | None:
        return self.repository.get(memory_type, key)

    def list(self, memory_type: MemoryType | None = None) -> builtins.list[Memory]:
        return self.repository.list_memories(memory_type)

    def search(self, query: str) -> builtins.list[Memory]:
        return self.repository.search(query)

    def forget(
        self, key: str, memory_type: MemoryType = MemoryType.SEMANTIC
    ) -> bool:
        memory = self.repository.get(memory_type, key)
        deleted = self.repository.delete(memory_type, key)
        if deleted:
            evidence_type = self.INFERENCE_EVIDENCE.get(key)
            if (
                memory is not None
                and memory.source is MemorySource.INFERRED
                and evidence_type is not None
                and self.events is not None
            ):
                self.events.delete_type(evidence_type)
            self._record(EventType.MEMORY_FORGOTTEN)
        return deleted

    def purge_expired(self) -> int:
        return self.repository.purge_expired()

    def _record(self, event_type: EventType) -> None:
        if self.events is not None:
            self.events.add(Event(event_type))
