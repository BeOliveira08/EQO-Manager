"""Contratos da inteligência local opcional."""

from eqo.ai.confirmation import ConfirmationGate
from eqo.ai.interface import AIProvider
from eqo.ai.models import (
    AIContextFact,
    AIInterpretation,
    AIMode,
    AIRequest,
    InterpretationDisposition,
    InterpretationOutcome,
)

__all__ = [
    "AIContextFact",
    "AIInterpretation",
    "AIMode",
    "AIProvider",
    "AIRequest",
    "InterpretationDisposition",
    "InterpretationOutcome",
    "ConfirmationGate",
]
