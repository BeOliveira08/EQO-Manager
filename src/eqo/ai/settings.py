import os
from dataclasses import dataclass

from eqo.ai.models import AIMode


@dataclass(frozen=True, slots=True)
class AISettings:
    mode: AIMode = AIMode.DISABLED
    ollama_host: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2:3b"
    timeout_seconds: float = 30.0

    @classmethod
    def from_environment(cls) -> "AISettings":
        raw_mode = os.getenv("EQO_AI_MODE", AIMode.DISABLED.value).casefold()
        valid_modes = {item.value for item in AIMode}
        mode = AIMode(raw_mode) if raw_mode in valid_modes else AIMode.DISABLED
        try:
            timeout = float(os.getenv("EQO_AI_TIMEOUT", "30"))
        except ValueError:
            timeout = 30.0
        return cls(
            mode=mode,
            ollama_host=os.getenv("EQO_OLLAMA_HOST", "http://127.0.0.1:11434"),
            ollama_model=os.getenv("EQO_OLLAMA_MODEL", "llama3.2:3b"),
            timeout_seconds=timeout,
        )
