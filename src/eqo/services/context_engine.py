from collections.abc import Callable
from datetime import UTC, datetime

from eqo.domain.context import Context
from eqo.domain.state import UserState


class ContextEngine:
    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self.clock = clock or (lambda: datetime.now(UTC))

    def current(
        self,
        state: UserState,
        *,
        available_minutes: int | None = None,
        current_activity: str | None = None,
    ) -> Context:
        return Context(
            current_time=self.clock(),
            available_minutes=(
                available_minutes
                if available_minutes is not None
                else state.available_minutes
            ),
            current_activity=current_activity,
        )

