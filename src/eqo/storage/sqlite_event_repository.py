import json
import sqlite3
from datetime import datetime
from pathlib import Path

from eqo.domain.event import Event, EventType


class SQLiteEventRepository:
    def __init__(self, database_path: str | Path = "data/eqo.db") -> None:
        self.path = Path(database_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    attributes TEXT NOT NULL
                )
            """)
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_type_time "
                "ON events(event_type, occurred_at)"
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def add(self, event: Event) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO events VALUES (?, ?, ?, ?)",
                (
                    event.id,
                    event.event_type.value,
                    event.occurred_at.isoformat(),
                    json.dumps(dict(event.attributes), ensure_ascii=False),
                ),
            )

    def list(self, event_type: EventType | None = None) -> list[Event]:
        query = "SELECT * FROM events"
        parameters: tuple[str, ...] = ()
        if event_type is not None:
            query += " WHERE event_type=?"
            parameters = (event_type.value,)
        query += " ORDER BY occurred_at"
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [Event(
            id=row["id"],
            event_type=EventType(row["event_type"]),
            occurred_at=datetime.fromisoformat(row["occurred_at"]),
            attributes=tuple(json.loads(row["attributes"]).items()),
        ) for row in rows]

    def delete_type(self, event_type: EventType) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM events WHERE event_type=?", (event_type.value,)
            )
        return cursor.rowcount
