from pathlib import Path

from eqo.domain.user import UserProfile
from eqo.services.profile_service import ProfileService
from eqo.storage.sqlite_profile_repository import SQLiteUserProfileRepository


def test_profile_is_persisted_updated_and_restored(tmp_path: Path) -> None:
    database = tmp_path / "eqo.db"
    first = ProfileService(SQLiteUserProfileRepository(database))
    first.save(UserProfile(name="Bernardo", age=30))
    updated = first.change_assistant_name("Alfred")
    restored = ProfileService(SQLiteUserProfileRepository(database)).current()
    assert updated.assistant_name == "Alfred"
    assert restored == updated
    assert restored is not None
    assert restored.language == "pt-BR"

