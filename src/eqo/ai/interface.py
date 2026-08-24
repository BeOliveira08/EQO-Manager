from typing import Protocol

from eqo.interaction.intent import ParsedCommand


class AIProvider(Protocol):
    """Fronteira futura; nenhuma implementação é exigida pelo Core."""

    def interpret(self, text: str) -> ParsedCommand: ...

