from pathlib import Path

from eqo.ai.confirmation import ConfirmationGate
from eqo.ai.context_builder import AIContextBuilder
from eqo.ai.interpreter import NaturalLanguageInterpreter
from eqo.ai.models import (
    AIInterpretation,
    AIMode,
    AIRequest,
    InterpretationDisposition,
)
from eqo.ai.ollama_provider import AIProviderUnavailable
from eqo.domain.state import Capacity, UserState
from eqo.interaction.intent import Intent
from eqo.services.memory_service import MemoryService
from eqo.storage.sqlite_memory_repository import SQLiteMemoryRepository


class FakeProvider:
    def __init__(self, result: AIInterpretation) -> None:
        self.result = result
        self.requests: list[AIRequest] = []

    def interpret(self, request: AIRequest) -> AIInterpretation:
        self.requests.append(request)
        return self.result


class UnavailableProvider:
    def interpret(self, request: AIRequest) -> AIInterpretation:
        raise AIProviderUnavailable("offline")


def test_thresholds_accept_confirm_and_reject_explicitly() -> None:
    for confidence, expected in [
        (0.9, InterpretationDisposition.ACCEPT),
        (0.7, InterpretationDisposition.CONFIRM),
        (0.4, InterpretationDisposition.UNKNOWN),
    ]:
        provider = FakeProvider(AIInterpretation(
            Intent.UPDATE_STATE, confidence, (("capacity", "LOW"),), "fake", "tiny"
        ))
        outcome = NaturalLanguageInterpreter(
            mode=AIMode.LOCAL, provider=provider
        ).interpret("não consigo estudar")
        assert outcome.disposition is expected


def test_confirmation_gate_never_accepts_without_user_confirmation() -> None:
    provider = FakeProvider(AIInterpretation(
        Intent.UPDATE_STATE, 0.7, (("capacity", "LOW"),), "fake", "tiny"
    ))
    outcome = NaturalLanguageInterpreter(mode=AIMode.LOCAL, provider=provider).interpret(
        "acho que não consigo"
    )
    rejected = ConfirmationGate().resolve(outcome, False)
    accepted = ConfirmationGate().resolve(outcome, True)
    assert rejected.disposition is InterpretationDisposition.UNKNOWN
    assert accepted.disposition is InterpretationDisposition.ACCEPT


def test_disabled_or_unavailable_ai_falls_back_while_explicit_commands_work() -> None:
    disabled = NaturalLanguageInterpreter(mode=AIMode.DISABLED)
    assert disabled.interpret("linguagem livre").disposition is InterpretationDisposition.UNKNOWN
    assert disabled.interpret("listar").interpretation.intent is Intent.LIST_TASKS
    unavailable = NaturalLanguageInterpreter(
        mode=AIMode.LOCAL, provider=UnavailableProvider()
    )
    fallback = unavailable.interpret("organiza meu dia")
    assert fallback.disposition is InterpretationDisposition.UNKNOWN


def test_context_builder_retrieves_only_relevant_limited_memories(tmp_path: Path) -> None:
    memories = MemoryService(SQLiteMemoryRepository(tmp_path / "eqo.db"))
    memories.remember("study_time", "estudar à noite")
    memories.remember("study_place", "estudar na biblioteca")
    memories.remember("coffee", "café sem açúcar")
    facts = AIContextBuilder(memories).build(
        "estudar", UserState(capacity=Capacity.LOW, available_minutes=30)
    )
    memory_facts = [fact for fact in facts if fact.source == "memory"]
    assert len(memory_facts) == 2
    assert {fact.key for fact in memory_facts} == {"study_time", "study_place"}
    assert any(fact.key == "capacity" and fact.value == "LOW" for fact in facts)
