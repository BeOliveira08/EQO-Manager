import json

import pytest

from eqo.ai.models import AIRequest
from eqo.ai.ollama_provider import AIProviderTimeout, OllamaAIProvider
from eqo.ai.validator import InvalidAIOutput
from eqo.interaction.intent import Intent

REQUEST = AIRequest("organiza meu dia", tuple(Intent))


def test_ollama_provider_uses_structured_local_request() -> None:
    captured: dict[str, object] = {}

    def transport(url: str, payload: bytes, timeout: float) -> bytes:
        captured.update(url=url, payload=json.loads(payload), timeout=timeout)
        content = json.dumps({
            "intent": "get_plan", "confidence": 0.93, "entities": {}
        })
        return json.dumps({"message": {"content": content}}).encode()

    provider = OllamaAIProvider(model="tiny:test", transport=transport, timeout_seconds=2)
    result = provider.interpret(REQUEST)
    assert result.intent is Intent.GET_PLAN
    assert result.provider == "ollama"
    assert captured["url"] == "http://127.0.0.1:11434/api/chat"
    assert captured["timeout"] == 2
    assert captured["payload"]["format"] == "json"  # type: ignore[index]
    assert captured["payload"]["stream"] is False  # type: ignore[index]


def test_ollama_timeout_and_invalid_envelope_are_explicit() -> None:
    def timeout(_url: str, _payload: bytes, _seconds: float) -> bytes:
        raise AIProviderTimeout("timeout")

    with pytest.raises(AIProviderTimeout):
        OllamaAIProvider(transport=timeout).interpret(REQUEST)
    with pytest.raises(InvalidAIOutput, match="HTTP"):
        OllamaAIProvider(transport=lambda *_args: b"{}").interpret(REQUEST)
