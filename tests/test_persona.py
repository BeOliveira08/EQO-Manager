import pytest

from eqo.domain.persona import (
    AutonomyLevel,
    Formality,
    Persona,
    Proactivity,
    Tone,
    Verbosity,
)
from eqo.domain.user import UserProfile


def test_persona_defaults_are_the_eqo_butler_configuration() -> None:
    persona = Persona()
    assert persona.name == "EQO"
    assert persona.role == "digital_butler"
    assert persona.tone is Tone.CALM
    assert persona.formality is Formality.MEDIUM
    assert persona.verbosity is Verbosity.CONCISE
    assert persona.proactivity is Proactivity.HIGH
    assert persona.autonomy is AutonomyLevel.SUGGESTIVE


def test_names_are_normalized_and_validated() -> None:
    assert Persona(name=" Alfred ").name == "Alfred"
    profile = UserProfile(name=" Bernardo ", assistant_name=" Alfred ")
    assert profile.name == "Bernardo"
    assert profile.assistant_name == "Alfred"
    with pytest.raises(ValueError, match="persona"):
        Persona(name=" ")

