import sqlite3
from pathlib import Path

from eqo.domain.state import Capacity, UserState


class SQLiteUserStateRepository:
    """Persiste o estado atual como singleton local no banco do EQO."""

    def __init__(self, database_path: str | Path = "data/eqo.db") -> None:
        self.path = Path(database_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS user_state (
                    singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
                    capacity INTEGER NOT NULL,
                    energy INTEGER NOT NULL,
                    available_minutes INTEGER NOT NULL,
                    focus INTEGER NOT NULL,
                    stress INTEGER NOT NULL
                )
            """)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def get(self) -> UserState | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM user_state WHERE singleton_id = 1"
            ).fetchone()
        if row is None:
            return None
        return UserState(
            capacity=Capacity(row["capacity"]),
            energy=row["energy"],
            available_minutes=row["available_minutes"],
            focus=row["focus"],
            stress=row["stress"],
        )

    def save(self, state: UserState) -> None:
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO user_state
                   (singleton_id, capacity, energy, available_minutes, focus, stress)
                   VALUES (1, ?, ?, ?, ?, ?)
                   ON CONFLICT(singleton_id) DO UPDATE SET
                   capacity=excluded.capacity, energy=excluded.energy,
                   available_minutes=excluded.available_minutes, focus=excluded.focus,
                   stress=excluded.stress""",
                (
                    int(state.capacity), state.energy, state.available_minutes,
                    state.focus, state.stress,
                ),
            )
