from dataclasses import dataclass

from eqo.interaction.response import InteractionResponse, ResponsePriority


@dataclass(frozen=True, slots=True)
class AccessibilityPresentation:
    announce: bool
    visual_alert: bool
    vibration_pattern: str | None
    emphasis: str


class AccessibilityPresenter:
    """Traduz metadata de apresentação; não altera texto nem decisão."""

    def present(self, response: InteractionResponse) -> AccessibilityPresentation:
        metadata = dict(response.accessibility_metadata)
        critical = response.priority >= ResponsePriority.HIGH or response.requires_attention
        return AccessibilityPresentation(
            announce=response.speech_allowed and (critical or metadata.get("announce") == "true"),
            visual_alert=response.display_allowed and critical,
            vibration_pattern=metadata.get("vibration") if critical else None,
            emphasis="strong" if critical else metadata.get("emphasis", "normal"),
        )
