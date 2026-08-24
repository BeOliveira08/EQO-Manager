import pytest

from eqo.accessibility.presenter import AccessibilityPresenter
from eqo.interaction.response import InteractionResponse, ResponsePriority


def test_high_priority_response_maps_to_accessible_channels() -> None:
    response = InteractionResponse(
        "Sua tarefa vence em 30 minutos.",
        priority=ResponsePriority.HIGH,
        requires_attention=True,
        accessibility_metadata=(("vibration", "urgent"),),
    )
    presentation = AccessibilityPresenter().present(response)
    assert presentation.announce is True
    assert presentation.visual_alert is True
    assert presentation.vibration_pattern == "urgent"
    assert presentation.emphasis == "strong"


def test_personality_text_is_not_changed_by_accessibility_mapping() -> None:
    response = InteractionResponse("Texto final", speech_allowed=False)
    presentation = AccessibilityPresenter().present(response)
    assert response.text == "Texto final"
    assert presentation.announce is False


def test_response_must_allow_at_least_one_output_channel() -> None:
    with pytest.raises(ValueError, match="canal"):
        InteractionResponse("Inacessível", speech_allowed=False, display_allowed=False)

