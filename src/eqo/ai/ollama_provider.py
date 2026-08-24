import json
import urllib.error
import urllib.request
from collections.abc import Callable

from eqo.ai.interface import AIProvider
from eqo.ai.models import AIInterpretation, AIRequest
from eqo.ai.prompt_builder import PromptBuilder
from eqo.ai.validator import AIOutputValidator, InvalidAIOutput


class AIProviderUnavailable(RuntimeError):
    pass


class AIProviderTimeout(RuntimeError):
    pass


Transport = Callable[[str, bytes, float], bytes]


class OllamaAIProvider(AIProvider):
    def __init__(
        self,
        model: str = "llama3.2:3b",
        host: str = "http://127.0.0.1:11434",
        timeout_seconds: float = 30.0,
        *,
        prompt_builder: PromptBuilder | None = None,
        validator: AIOutputValidator | None = None,
        transport: Transport | None = None,
    ) -> None:
        self.model = model
        self.host = host.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.validator = validator or AIOutputValidator()
        self.transport = transport or self._post

    def interpret(self, request: AIRequest) -> AIInterpretation:
        payload = json.dumps({
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "user", "content": self.prompt_builder.build(request)}
            ],
            "options": {"temperature": 0},
        }).encode("utf-8")
        raw_response = self.transport(
            f"{self.host}/api/chat", payload, self.timeout_seconds
        )
        try:
            envelope = json.loads(raw_response.decode("utf-8"))
            content = envelope["message"]["content"]
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as error:
            raise InvalidAIOutput("A resposta HTTP do Ollama é inválida.") from error
        if not isinstance(content, str):
            raise InvalidAIOutput("O conteúdo retornado pelo Ollama não é texto JSON.")
        return self.validator.parse_and_validate(
            content, request, provider="ollama", model=self.model
        )

    @staticmethod
    def _post(url: str, payload: bytes, timeout: float) -> bytes:
        request = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return bytes(response.read())
        except TimeoutError as error:
            raise AIProviderTimeout("O modelo local excedeu o tempo limite.") from error
        except (urllib.error.URLError, OSError) as error:
            raise AIProviderUnavailable("O Ollama local está indisponível.") from error
