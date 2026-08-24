from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from eqo.storage.repositories import (
    EventRepository,
    MemoryRepository,
    TaskRepository,
    UserProfileRepository,
    UserStateRepository,
)


class LogicalBackupService:
    """Exporta entidades estáveis, nunca páginas ou arquivos internos do SQLite."""

    FORMAT = "eqo.logical-backup"
    SCHEMA_VERSION = 1

    def __init__(
        self,
        tasks: TaskRepository,
        states: UserStateRepository,
        profiles: UserProfileRepository,
        memories: MemoryRepository,
        events: EventRepository,
    ) -> None:
        self.tasks = tasks
        self.states = states
        self.profiles = profiles
        self.memories = memories
        self.events = events

    def payload(self, exported_at: datetime | None = None) -> dict[str, Any]:
        stamp = exported_at or datetime.now(UTC)
        if stamp.tzinfo is None:
            raise ValueError("A data da exportação deve possuir fuso horário.")
        state = self.states.get()
        profile = self.profiles.get()
        return {
            "format": self.FORMAT,
            "schema_version": self.SCHEMA_VERSION,
            "exported_at": stamp.isoformat(),
            "data": {
                "tasks": [self._task(item) for item in self.tasks.list()],
                "state": None if state is None else {
                    "capacity": int(state.capacity), "energy": state.energy,
                    "available_minutes": state.available_minutes,
                    "focus": state.focus, "stress": state.stress,
                },
                "profile": None if profile is None else {
                    "name": profile.name, "assistant_name": profile.assistant_name,
                    "age": profile.age, "language": profile.language,
                    "timezone": profile.timezone,
                },
                "memories": [self._memory(item) for item in self.memories.list_memories()],
                "events": [self._event(item) for item in self.events.list()],
            },
        }

    def export(self, destination: str | Path, exported_at: datetime | None = None) -> Path:
        path = Path(destination)
        if path.suffix != ".eqobackup":
            raise ValueError("O backup lógico deve usar a extensão .eqobackup.")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.payload(exported_at), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    @staticmethod
    def _task(item: Any) -> dict[str, Any]:
        return {
            "id": item.id, "title": item.title, "description": item.description,
            "status": item.status.value, "priority": int(item.priority),
            "deadline": item.deadline.isoformat() if item.deadline else None,
            "estimated_minutes": item.estimated_minutes, "effort": item.effort,
            "flexibility": item.flexibility, "context": item.context,
            "created_at": item.created_at.isoformat(),
            "completed_at": item.completed_at.isoformat() if item.completed_at else None,
        }

    @staticmethod
    def _memory(item: Any) -> dict[str, Any]:
        return {
            "id": item.id, "type": item.memory_type.value, "key": item.key,
            "value": item.value, "importance": int(item.importance),
            "confidence": item.confidence, "source": item.source.value,
            "created_at": item.created_at.isoformat(), "updated_at": item.updated_at.isoformat(),
            "expires_at": item.expires_at.isoformat() if item.expires_at else None,
        }

    @staticmethod
    def _event(item: Any) -> dict[str, Any]:
        return {
            "id": item.id, "type": item.event_type.value,
            "occurred_at": item.occurred_at.isoformat(), "attributes": dict(item.attributes),
        }
