from dataclasses import dataclass
from enum import StrEnum

from eqo.interaction.intent import Intent


class AIMode(StrEnum):
    DISABLED = "disabled"
    LOCAL = "local"


class InterpretationDisposition(StrEnum):
    ACCEPT = "accept"
    CONFIRM = "confirm"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class AIContextFact:
    source: str
    key: str
    value: str


@dataclass(frozen=True, slots=True)
class AIRequest:
    text: str
    allowed_intents: tuple[Intent, ...]
    context: tuple[AIContextFact, ...] = ()

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("O texto para interpretação não pode estar vazio.")
        if not self.allowed_intents:
            raise ValueError("Ao menos uma intent deve ser permitida.")


@dataclass(frozen=True, slots=True)
class AIInterpretation:
    intent: Intent
    confidence: float
    entities: tuple[tuple[str, str], ...] = ()
    provider: str = "unknown"
    model: str = "unknown"

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("A confiança do modelo deve estar entre 0 e 1.")
        keys = [key for key, _ in self.entities]
        if len(keys) != len(set(keys)):
            raise ValueError("Entidades não podem repetir chaves.")

    def entity(self, key: str) -> str | None:
        return dict(self.entities).get(key)


@dataclass(frozen=True, slots=True)
class InterpretationOutcome:
    disposition: InterpretationDisposition
    interpretation: AIInterpretation

