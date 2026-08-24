from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Context:
    current_time: datetime
    available_minutes: int
    current_activity: str | None = None

    def __post_init__(self) -> None:
        if self.current_time.tzinfo is None:
            raise ValueError("O horário do contexto deve possuir fuso horário.")
        if self.available_minutes < 0:
            raise ValueError("O tempo disponível não pode ser negativo.")
        if self.current_activity is not None:
            normalized = self.current_activity.strip()
            object.__setattr__(self, "current_activity", normalized or None)

    @property
    def day_of_week(self) -> int:
        """Dia ISO: segunda-feira=1, domingo=7."""
        return self.current_time.isoweekday()

