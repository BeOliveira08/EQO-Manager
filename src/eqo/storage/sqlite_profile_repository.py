import sqlite3
from pathlib import Path

from eqo.domain.user import UserProfile


class SQLiteUserProfileRepository:
    def __init__(self, database_path: str | Path = "data/eqo.db") -> None:
        self.path = Path(database_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS user_profile (
                    singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
                    name TEXT NOT NULL,
                    assistant_name TEXT NOT NULL,
                    age INTEGER,
                    language TEXT NOT NULL,
                    timezone TEXT NOT NULL
                )
            """)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def get(self) -> UserProfile | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM user_profile WHERE singleton_id = 1"
            ).fetchone()
        if row is None:
            return None
        return UserProfile(
            name=row["name"],
            assistant_name=row["assistant_name"],
            age=row["age"],
            language=row["language"],
            timezone=row["timezone"],
        )

    def save(self, profile: UserProfile) -> None:
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO user_profile
                   (singleton_id, name, assistant_name, age, language, timezone)
                   VALUES (1, ?, ?, ?, ?, ?)
                   ON CONFLICT(singleton_id) DO UPDATE SET
                   name=excluded.name, assistant_name=excluded.assistant_name,
                   age=excluded.age, language=excluded.language,
                   timezone=excluded.timezone""",
                (
                    profile.name,
                    profile.assistant_name,
                    profile.age,
                    profile.language,
                    profile.timezone,
                ),
            )
