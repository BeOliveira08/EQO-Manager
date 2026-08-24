from dataclasses import dataclass
from enum import StrEnum


class Tone(StrEnum):
    CALM = "calm"
    WARM = "warm"
    DIRECT = "direct"


class Formality(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Verbosity(StrEnum):
    CONCISE = "concise"
    BALANCED = "balanced"


class Proactivity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AutonomyLevel(StrEnum):
    PASSIVE = "passive"
    SUGGESTIVE = "suggestive"
    CONFIRM = "confirm"
    AUTONOMOUS = "autonomous"


@dataclass(frozen=True, slots=True)
class Persona:
    name: str = "EQO"
    role: str = "digital_butler"
    tone: Tone = Tone.CALM
    formality: Formality = Formality.MEDIUM
    verbosity: Verbosity = Verbosity.CONCISE
    proactivity: Proactivity = Proactivity.HIGH
    autonomy: AutonomyLevel = AutonomyLevel.SUGGESTIVE

    def __post_init__(self) -> None:
        normalized_name = self.name.strip()
        if not normalized_name:
            raise ValueError("O nome da persona não pode estar vazio.")
        if not self.role.strip():
            raise ValueError("O papel da persona não pode estar vazio.")
        object.__setattr__(self, "name", normalized_name)

