from __future__ import annotations

import json
import sqlite3
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from eqo.domain.task import Priority, Task, TaskStatus


class SQLiteTaskRepository:
    def __init__(self, database_path: str | Path = "data/eqo.db") -> None:
        self.path = Path(database_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    deadline TEXT,
                    estimated_minutes INTEGER,
                    effort INTEGER NOT NULL,
                    flexibility INTEGER NOT NULL,
                    context TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                )
            """)

    def add(self, task: Task) -> None:
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                self._values(task),
            )

    def save(self, task: Task) -> None:
        with self._connect() as connection:
            connection.execute(
                """UPDATE tasks SET title=?, description=?, status=?, priority=?, deadline=?,
                   estimated_minutes=?, effort=?, flexibility=?, context=?, created_at=?,
                   completed_at=? WHERE id=?""",
                (*self._values(task)[1:], task.id),
            )

    def get(self, task_id: str) -> Task | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return self._from_row(row) if row else None

    def list(self, status: TaskStatus | None = None) -> list[Task]:
        query = "SELECT * FROM tasks"
        parameters: tuple[str, ...] = ()
        if status is not None:
            query += " WHERE status = ?"
            parameters = (status.value,)
        query += " ORDER BY priority, deadline IS NULL, deadline, created_at"
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [self._from_row(row) for row in rows]

    def remove(self, task_id: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        return cursor.rowcount > 0

    def count(self) -> int:
        with self._connect() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0])

    def backup_to(self, directory: str | Path) -> Path | None:
        if self.count() == 0:
            return None
        backup_directory = Path(directory)
        backup_directory.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")
        destination = backup_directory / f"eqo_backup_{stamp}.db"
        with self._connect() as source, sqlite3.connect(destination) as target:
            source.backup(target)
        return destination

    def import_legacy_json(self, path: str | Path) -> int:
        legacy_path = Path(path)
        if not legacy_path.exists() or self.count() > 0:
            return 0
        try:
            payload: list[dict[str, Any]] = json.loads(
                legacy_path.read_text(encoding="utf-8")
            )
        except (json.JSONDecodeError, OSError):
            return 0
        imported = 0
        for item in payload:
            deadline = date.fromisoformat(item["deadline"]) if item.get("deadline") else None
            task = Task(
                title=str(item["title"]),
                priority=Priority(int(item.get("priority", 2))),
                deadline=deadline,
            )
            if item.get("completed"):
                task.complete()
            self.add(task)
            imported += 1
        return imported

    @staticmethod
    def _values(task: Task) -> tuple[object, ...]:
        return (
            task.id, task.title, task.description, task.status.value, int(task.priority),
            task.deadline.isoformat() if task.deadline else None, task.estimated_minutes,
            task.effort, task.flexibility, task.context, task.created_at.isoformat(),
            task.completed_at.isoformat() if task.completed_at else None,
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Task:
        created_at = datetime.fromisoformat(row["created_at"])
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)
        return Task(
            id=row["id"], title=row["title"], description=row["description"],
            status=TaskStatus(row["status"]), priority=Priority(row["priority"]),
            deadline=date.fromisoformat(row["deadline"]) if row["deadline"] else None,
            estimated_minutes=row["estimated_minutes"], effort=row["effort"],
            flexibility=row["flexibility"], context=row["context"], created_at=created_at,
            completed_at=(datetime.fromisoformat(row["completed_at"])
                          if row["completed_at"] else None),
        )
