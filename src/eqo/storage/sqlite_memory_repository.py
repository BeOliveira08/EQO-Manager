from __future__ import annotations

import sqlite3
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from eqo.domain.memory import (
    Memory,
    MemoryImportance,
    MemorySource,
    MemoryType,
)


class SQLiteMemoryRepository:
    def __init__(self, database_path: str | Path = "data/eqo.db") -> None:
        self.path = Path(database_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    memory_type TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    importance INTEGER NOT NULL,
                    confidence REAL NOT NULL,
                    source TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    expires_at TEXT,
                    UNIQUE(memory_type, key)
                )
            """)
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_memories_expiry ON memories(expires_at)"
            )
            connection.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts
                USING fts5(memory_id UNINDEXED, key, value)
            """)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def upsert(self, memory: Memory) -> Memory:
        now = datetime.now(UTC)
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT id, created_at FROM memories WHERE memory_type=? AND key=?",
                (memory.memory_type.value, memory.key),
            ).fetchone()
            stored = replace(
                memory,
                id=existing["id"] if existing else memory.id,
                created_at=(
                    datetime.fromisoformat(existing["created_at"])
                    if existing else memory.created_at
                ),
                updated_at=now,
            )
            connection.execute(
                """INSERT INTO memories VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(memory_type, key) DO UPDATE SET
                   value=excluded.value, importance=excluded.importance,
                   confidence=excluded.confidence, source=excluded.source,
                   updated_at=excluded.updated_at, expires_at=excluded.expires_at""",
                self._values(stored),
            )
            connection.execute("DELETE FROM memory_fts WHERE memory_id=?", (stored.id,))
            connection.execute(
                "INSERT INTO memory_fts(memory_id, key, value) VALUES (?, ?, ?)",
                (stored.id, stored.key, stored.value),
            )
        return stored

    def get(self, memory_type: MemoryType, key: str) -> Memory | None:
        with self._connect() as connection:
            row = connection.execute(
                """SELECT * FROM memories WHERE memory_type=? AND key=?
                   AND (expires_at IS NULL OR expires_at > ?)""",
                (memory_type.value, key.strip(), datetime.now(UTC).isoformat()),
            ).fetchone()
        return self._from_row(row) if row else None

    def list_memories(self, memory_type: MemoryType | None = None) -> list[Memory]:
        query = "SELECT * FROM memories WHERE (expires_at IS NULL OR expires_at > ?)"
        parameters: list[object] = [datetime.now(UTC).isoformat()]
        if memory_type is not None:
            query += " AND memory_type=?"
            parameters.append(memory_type.value)
        query += " ORDER BY importance DESC, updated_at DESC"
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [self._from_row(row) for row in rows]

    def search(self, query: str) -> list[Memory]:
        tokens = query.replace('"', " ").split()
        if not tokens:
            return []
        expression = " ".join(f'"{token}"' for token in tokens)
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT m.* FROM memory_fts f
                   JOIN memories m ON m.id=f.memory_id
                   WHERE memory_fts MATCH ?
                   AND (m.expires_at IS NULL OR m.expires_at > ?)
                   ORDER BY m.importance DESC, m.updated_at DESC""",
                (expression, datetime.now(UTC).isoformat()),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def delete(self, memory_type: MemoryType, key: str) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id FROM memories WHERE memory_type=? AND key=?",
                (memory_type.value, key.strip()),
            ).fetchone()
            if row is None:
                return False
            connection.execute("DELETE FROM memory_fts WHERE memory_id=?", (row["id"],))
            connection.execute("DELETE FROM memories WHERE id=?", (row["id"],))
        return True

    def purge_expired(self) -> int:
        now = datetime.now(UTC).isoformat()
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id FROM memories WHERE expires_at IS NOT NULL AND expires_at <= ?",
                (now,),
            ).fetchall()
            for row in rows:
                connection.execute(
                    "DELETE FROM memory_fts WHERE memory_id=?", (row["id"],)
                )
            connection.execute(
                "DELETE FROM memories WHERE expires_at IS NOT NULL AND expires_at <= ?",
                (now,),
            )
        return len(rows)

    @staticmethod
    def _values(memory: Memory) -> tuple[object, ...]:
        return (
            memory.id,
            memory.memory_type.value,
            memory.key,
            memory.value,
            int(memory.importance),
            memory.confidence,
            memory.source.value,
            memory.created_at.isoformat(),
            memory.updated_at.isoformat(),
            memory.expires_at.isoformat() if memory.expires_at else None,
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Memory:
        return Memory(
            id=row["id"],
            memory_type=MemoryType(row["memory_type"]),
            key=row["key"],
            value=row["value"],
            importance=MemoryImportance(row["importance"]),
            confidence=row["confidence"],
            source=MemorySource(row["source"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            expires_at=(
                datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None
            ),
        )
