from dataclasses import replace

from eqo.domain.state import Capacity, UserState
from eqo.storage.repositories import UserStateRepository


class StateService:
    def __init__(self, repository: UserStateRepository) -> None:
        self.repository = repository

    def current(self) -> UserState:
        return self.repository.get() or UserState()

    def update(
        self,
        *,
        capacity: Capacity | None = None,
        energy: int | None = None,
        available_minutes: int | None = None,
        focus: int | None = None,
        stress: int | None = None,
    ) -> UserState:
        current = self.current()
        updated = replace(
            current,
            capacity=capacity if capacity is not None else current.capacity,
            energy=energy if energy is not None else current.energy,
            available_minutes=(
                available_minutes
                if available_minutes is not None
                else current.available_minutes
            ),
            focus=focus if focus is not None else current.focus,
            stress=stress if stress is not None else current.stress,
        )
        self.repository.save(updated)
        return updated
