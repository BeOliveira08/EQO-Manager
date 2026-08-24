from pathlib import Path

import pytest

from eqo.services.dialogue_manager import ConversationState, DialogueManager
from eqo.services.profile_service import ProfileService
from eqo.storage.sqlite_profile_repository import SQLiteUserProfileRepository


def make_dialogue(tmp_path: Path) -> tuple[DialogueManager, ProfileService]:
    profiles = ProfileService(SQLiteUserProfileRepository(tmp_path / "eqo.db"))
    return DialogueManager(profiles), profiles


def assert_state(dialogue: DialogueManager, expected: ConversationState) -> None:
    assert dialogue.state is expected


def test_onboarding_persists_user_and_custom_assistant_name(tmp_path: Path) -> None:
    dialogue, profiles = make_dialogue(tmp_path)
    assert "Como posso chamar" in dialogue.start_onboarding().text
    assert_state(dialogue, ConversationState.ASK_USER_NAME)
    assert "Prazer, Bernardo" in dialogue.receive("Bernardo").text
    assert_state(dialogue, ConversationState.ASK_ASSISTANT_NAME)
    assert "eu sou Alfred" in dialogue.receive("Alfred").text
    assert_state(dialogue, ConversationState.CONFIRM)
    assert dialogue.receive("sim").requires_confirmation is False
    assert_state(dialogue, ConversationState.READY)
    profile = profiles.current()
    assert profile is not None
    assert profile.assistant_name == "Alfred"


def test_onboarding_can_restart_after_rejected_confirmation(tmp_path: Path) -> None:
    dialogue, _ = make_dialogue(tmp_path)
    dialogue.start_onboarding()
    dialogue.receive("Bernardo")
    dialogue.receive("sim")
    response = dialogue.receive("não")
    assert dialogue.state is ConversationState.ASK_USER_NAME
    assert "Como posso chamar" in response.text


def test_dialogue_rejects_input_before_start_and_keeps_invalid_state(tmp_path: Path) -> None:
    dialogue, _ = make_dialogue(tmp_path)
    with pytest.raises(RuntimeError, match="iniciado"):
        dialogue.receive("Bernardo")
    dialogue.start_onboarding()
    dialogue.receive("Bernardo")
    dialogue.receive("EQO")
    response = dialogue.receive("talvez")
    assert dialogue.state is ConversationState.CONFIRM
    assert "confirmar" in response.text
