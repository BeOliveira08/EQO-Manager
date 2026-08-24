from dataclasses import dataclass
from enum import IntEnum


class Capacity(IntEnum):
    VERY_LOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    VERY_HIGH = 5


@dataclass(frozen=True, slots=True)
class UserState:
    capacity: Capacity = Capacity.MEDIUM
    energy: int = 3
    available_minutes: int = 0
    focus: int = 3
    stress: int = 3

    def __post_init__(self) -> None:
        if self.available_minutes < 0:
            raise ValueError("O tempo disponível não pode ser negativo.")
        if not all(1 <= value <= 5 for value in (self.energy, self.focus, self.stress)):
            raise ValueError("Energia, foco e estresse devem estar entre 1 e 5.")
