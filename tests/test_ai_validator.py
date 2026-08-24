import json

import pytest

from eqo.ai.models import AIRequest
from eqo.ai.validator import AIOutputValidator, InvalidAIOutput
from eqo.interaction.intent import Intent

REQUEST = AIRequest("estou cansado", tuple(Intent))


def validate(payload: object):  # type: ignore[no-untyped-def]
    return AIOutputValidator().parse_and_validate(
        json.dumps(payload), REQUEST, provider="fake", model="test"
    )


def test_valid_structured_interpretation_is_typed() -> None:
    result = validate({
        "intent": "update_state",
        "confidence": 0.91,
        "entities": {"capacity": "LOW"},
    })
    assert result.intent is Intent.UPDATE_STATE
    assert result.confidence == 0.91
    assert result.entity("capacity") == "LOW"


@pytest.mark.parametrize("payload", [
    {"intent": "order_pizza", "confidence": 0.9, "entities": {}},
    {"intent": "update_state", "confidence": 1.2, "entities": {"capacity": "LOW"}},
    {"intent": "update_state", "confidence": 0.9, "entities": {"capacity": "EXHAUSTED"}},
    {"intent": "get_plan", "confidence": 0.9, "entities": {"shell": "rm"}},
    {"intent": "create_task", "confidence": 0.9, "entities": {}},
    {"intent": "create_task", "confidence": 0.9,
     "entities": {"title": "X", "priority": "URGENT"}},
    {"intent": "create_task", "confidence": 0.9,
     "entities": {"title": "X", "deadline": "amanhã"}},
    {"intent": "update_state", "confidence": True, "entities": {"capacity": "LOW"}},
])
def test_invalid_intent_confidence_entity_or_schema_is_rejected(payload: object) -> None:
    with pytest.raises(InvalidAIOutput):
        validate(payload)


def test_invalid_json_and_free_text_are_rejected() -> None:
    validator = AIOutputValidator()
    for output in ["Claro, vou cuidar disso.", "```json\n{}\n```", "{invalid"]:
        with pytest.raises(InvalidAIOutput, match="JSON"):
            validator.parse_and_validate(
                output, REQUEST, provider="fake", model="test"
            )
