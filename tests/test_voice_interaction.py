from pathlib import Path

from eqo.ai.interpreter import NaturalLanguageInterpreter
from eqo.ai.models import AIInterpretation, AIMode, AIRequest
from eqo.ai.ollama_provider import AIProviderUnavailable
from eqo.domain.state import Capacity
from eqo.interaction.intent import Intent
from eqo.services.dialogue_manager import ConversationState, DialogueManager
from eqo.services.interpretation_executor import InterpretationExecutor
from eqo.services.memory_service import MemoryService
from eqo.services.profile_service import ProfileService
from eqo.services.state_service import StateService
from eqo.services.task_service import TaskService
from eqo.services.voice_interaction import VoiceInteractionService
from eqo.speech.errors import STTUnavailable, TTSUnavailable
from eqo.speech.interfaces import AudioInput
from eqo.storage.sqlite_memory_repository import SQLiteMemoryRepository
from eqo.storage.sqlite_profile_repository import SQLiteUserProfileRepository
from eqo.storage.sqlite_repository import SQLiteTaskRepository
from eqo.storage.sqlite_state_repository import SQLiteUserStateRepository


class FakeSTT:
    def __init__(self, text: str = "organiza meu dia", *, fail: bool = False) -> None:
        self.text = text
        self.fail = fail
        self.calls = 0

    def transcribe(self, audio: AudioInput) -> str:
        self.calls += 1
        if self.fail:
            raise STTUnavailable("offline")
        return self.text


class FakeTTS:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.spoken: list[str] = []

    def speak(self, text: str) -> None:
        if self.fail:
            raise TTSUnavailable("offline")
        self.spoken.append(text)


class FakeAI:
    def __init__(self, interpretation: AIInterpretation) -> None:
        self.interpretation = interpretation
        self.calls = 0

    def interpret(self, request: AIRequest) -> AIInterpretation:
        self.calls += 1
        return self.interpretation


class OfflineAI:
    def interpret(self, request: AIRequest) -> AIInterpretation:
        raise AIProviderUnavailable("offline")


def build_voice(
    tmp_path: Path,
    stt: FakeSTT,
    provider: FakeAI | OfflineAI,
    tts: FakeTTS | None = None,
) -> tuple[VoiceInteractionService, StateService]:
    database = tmp_path / "eqo.db"
    tasks = TaskService(SQLiteTaskRepository(database))
    states = StateService(SQLiteUserStateRepository(database))
    memories = MemoryService(SQLiteMemoryRepository(database))
    profiles = ProfileService(SQLiteUserProfileRepository(database))
    dialogue = DialogueManager(profiles)
    executor = InterpretationExecutor(tasks=tasks, states=states, memories=memories)
    interpreter = NaturalLanguageInterpreter(mode=AIMode.LOCAL, provider=provider)
    return VoiceInteractionService(
        stt=stt,
        interpreter=interpreter,
        executor=executor,
        dialogue=dialogue,
        states=states,
        tts=tts,
    ), states


def test_voice_pipeline_transcribes_executes_and_speaks_final_response(tmp_path: Path) -> None:
    tts = FakeTTS()
    voice, _ = build_voice(
        tmp_path,
        FakeSTT(),
        FakeAI(AIInterpretation(Intent.LIST_TASKS, 0.95, provider="fake")),
        tts,
    )
    result = voice.process(AudioInput(b"RIFFvoice"))
    assert result.transcript == "organiza meu dia"
    assert "0 tarefa" in result.response.text
    assert tts.spoken == [result.response.text]
    assert result.state is ConversationState.IDLE
    assert result.metrics.total_ms >= result.metrics.core_ms


def test_voice_confirmation_does_not_call_ai_again(tmp_path: Path) -> None:
    provider = FakeAI(AIInterpretation(
        Intent.UPDATE_STATE, 0.7, (("capacity", "LOW"),), "fake", "tiny"
    ))
    voice, states = build_voice(tmp_path, FakeSTT("estou cansado"), provider, FakeTTS())
    pending = voice.process(AudioInput(b"RIFFvoice"))
    assert pending.state is ConversationState.WAITING_CONFIRMATION
    assert pending.response.requires_confirmation is True
    completed = voice.confirm_text("sim")
    assert completed.state is ConversationState.IDLE
    assert states.current().capacity is Capacity.LOW
    assert provider.calls == 1


def test_voice_confirmation_audio_is_transcribed_without_ai_reinterpretation(
    tmp_path: Path,
) -> None:
    stt = FakeSTT("estou cansado")
    provider = FakeAI(AIInterpretation(
        Intent.UPDATE_STATE, 0.7, (("capacity", "LOW"),), "fake", "tiny"
    ))
    voice, states = build_voice(tmp_path, stt, provider)
    voice.process(AudioInput(b"RIFFrequest"))
    stt.text = "sim"
    result = voice.confirm(AudioInput(b"RIFFconfirmation"))
    assert result.state is ConversationState.IDLE
    assert states.current().capacity is Capacity.LOW
    assert stt.calls == 2
    assert provider.calls == 1


def test_stt_failure_preserves_text_fallback_and_never_executes(tmp_path: Path) -> None:
    provider = FakeAI(AIInterpretation(Intent.UPDATE_STATE, 0.99, (("capacity", "LOW"),)))
    voice, states = build_voice(tmp_path, FakeSTT(fail=True), provider)
    result = voice.process(AudioInput(b"RIFFvoice"))
    assert result.state is ConversationState.ERROR
    assert result.metrics.stt_failed is True
    assert result.response.display_allowed is True
    assert states.current().capacity is Capacity.MEDIUM
    assert provider.calls == 0


def test_tts_failure_keeps_final_text_available(tmp_path: Path) -> None:
    voice, _ = build_voice(
        tmp_path,
        FakeSTT(),
        FakeAI(AIInterpretation(Intent.LIST_TASKS, 0.95)),
        FakeTTS(fail=True),
    )
    result = voice.process(AudioInput(b"RIFFvoice"))
    assert result.metrics.tts_failed is True
    assert result.response.text
    assert result.response.display_allowed is True


def test_ai_offline_falls_back_without_breaking_voice_or_core(tmp_path: Path) -> None:
    voice, states = build_voice(tmp_path, FakeSTT(), OfflineAI(), FakeTTS())
    result = voice.process(AudioInput(b"RIFFvoice"))
    assert "Nenhuma ação" in result.response.text
    assert states.current().capacity is Capacity.MEDIUM
