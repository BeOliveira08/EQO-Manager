from pathlib import Path

import pytest

from eqo.domain.state import Capacity, UserState
from eqo.services.state_service import StateService
from eqo.storage.sqlite_state_repository import SQLiteUserStateRepository


def test_state_is_persisted_and_updated_across_instances(tmp_path: Path) -> None:
    database = tmp_path / "eqo.db"
    first = StateService(SQLiteUserStateRepository(database))
    assert first.current() == UserState()
    first.update(
        capacity=Capacity.LOW,
        energy=2,
        available_minutes=45,
        focus=2,
        stress=4,
    )
    restored = StateService(SQLiteUserStateRepository(database)).current()
    assert restored == UserState(
        capacity=Capacity.LOW,
        energy=2,
        available_minutes=45,
        focus=2,
        stress=4,
    )


def test_state_rejects_out_of_range_dimensions() -> None:
    with pytest.raises(ValueError, match="entre 1 e 5"):
        UserState(energy=0)

