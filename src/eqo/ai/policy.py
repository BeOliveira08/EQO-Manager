from dataclasses import dataclass

from eqo.ai.models import (
    AIInterpretation,
    InterpretationDisposition,
    InterpretationOutcome,
)
from eqo.interaction.intent import Intent


@dataclass(frozen=True, slots=True)
class AIConfidencePolicy:
    accept_threshold: float = 0.8
    confirm_threshold: float = 0.5

    def __post_init__(self) -> None:
        if not 0 <= self.confirm_threshold <= self.accept_threshold <= 1:
            raise ValueError("Os thresholds de confiança são inválidos.")

    def evaluate(self, interpretation: AIInterpretation) -> InterpretationOutcome:
        if interpretation.intent is Intent.UNKNOWN:
            disposition = InterpretationDisposition.UNKNOWN
        elif interpretation.confidence >= self.accept_threshold:
            disposition = InterpretationDisposition.ACCEPT
        elif interpretation.confidence >= self.confirm_threshold:
            disposition = InterpretationDisposition.CONFIRM
        else:
            disposition = InterpretationDisposition.UNKNOWN
        return InterpretationOutcome(disposition, interpretation)
