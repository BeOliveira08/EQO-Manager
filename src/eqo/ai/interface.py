from typing import Protocol

from eqo.ai.models import AIInterpretation, AIRequest


class AIProvider(Protocol):
    """Um provider interpreta linguagem; nunca recebe repositórios ou executa ações."""

    def interpret(self, request: AIRequest) -> AIInterpretation: ...
