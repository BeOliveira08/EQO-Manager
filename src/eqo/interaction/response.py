from dataclasses import dataclass
from enum import IntEnum

from eqo.domain.decision import Decision
from eqo.interaction.intent import Intent


class ResponsePriority(IntEnum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass(frozen=True, slots=True)
class InteractionResponse:
    text: str
    intent: Intent | None = None
    decision: Decision | None = None
    reason: str | None = None
    requires_confirmation: bool = False
    priority: ResponsePriority = ResponsePriority.NORMAL
    requires_attention: bool = False
    speech_allowed: bool = True
    display_allowed: bool = True
    accessibility_metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("Uma resposta precisa possuir texto.")
        if self.decision is not None and not self.reason:
            raise ValueError("Respostas ligadas a decisões devem preservar a justificativa.")
        keys = [key for key, _ in self.accessibility_metadata]
        if len(keys) != len(set(keys)):
            raise ValueError("Metadados de acessibilidade não podem repetir chaves.")
        if not self.speech_allowed and not self.display_allowed:
            raise ValueError("A resposta precisa permitir ao menos um canal de apresentação.")


@dataclass(frozen=True, slots=True)
class ProactiveMessage:
    text: str
    trigger: str
    requires_confirmation: bool = False
