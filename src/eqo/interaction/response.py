from dataclasses import dataclass

from eqo.domain.decision import Decision
from eqo.interaction.intent import Intent


@dataclass(frozen=True, slots=True)
class InteractionResponse:
    text: str
    intent: Intent | None = None
    decision: Decision | None = None
    reason: str | None = None
    requires_confirmation: bool = False

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("Uma resposta precisa possuir texto.")
        if self.decision is not None and not self.reason:
            raise ValueError("Respostas ligadas a decisões devem preservar a justificativa.")


@dataclass(frozen=True, slots=True)
class ProactiveMessage:
    text: str
    trigger: str
    requires_confirmation: bool = False

