from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import IntEnum, StrEnum
from uuid import uuid4


class MemoryType(StrEnum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"


class MemoryImportance(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class MemorySource(StrEnum):
    USER_EXPLICIT = "user_explicit"
    SYSTEM_EVENT = "system_event"
    USER_PREFERENCE = "user_preference"
    INFERRED = "inferred"
    IMPORTED = "imported"


@dataclass(frozen=True, slots=True)
class Memory:
    key: str
    value: str
    memory_type: MemoryType = MemoryType.SEMANTIC
    importance: MemoryImportance = MemoryImportance.MEDIUM
    confidence: float = 1.0
    source: MemorySource = MemorySource.USER_EXPLICIT
    expires_at: datetime | None = None
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        key = self.key.strip()
        value = self.value.strip()
        if not key or not value:
            raise ValueError("Chave e valor da memória são obrigatórios.")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("A confiança deve estar entre 0 e 1.")
        for instant in (self.created_at, self.updated_at, self.expires_at):
            if instant is not None and instant.tzinfo is None:
                raise ValueError("Datas de memória devem possuir fuso horário.")
        object.__setattr__(self, "key", key)
        object.__setattr__(self, "value", value)

    def is_expired(self, now: datetime | None = None) -> bool:
        return self.expires_at is not None and self.expires_at <= (now or datetime.now(UTC))

