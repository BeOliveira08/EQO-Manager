from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter

from eqo.ai.confirmation import ConfirmationGate
from eqo.ai.interpreter import NaturalLanguageInterpreter
from eqo.ai.models import InterpretationDisposition, InterpretationOutcome
from eqo.interaction.response import InteractionResponse, ResponsePriority
from eqo.services.dialogue_manager import ConversationState, DialogueManager
from eqo.services.interpretation_executor import InterpretationExecutor
from eqo.services.state_service import StateService
from eqo.speech.errors import SpeechError
from eqo.speech.interfaces import AudioInput, STTProvider, TTSProvider


@dataclass(frozen=True, slots=True)
class VoicePipelineMetrics:
    stt_ms: float = 0.0
    interpretation_ms: float = 0.0
    core_ms: float = 0.0
    tts_ms: float = 0.0
    total_ms: float = 0.0
    stt_failed: bool = False
    tts_failed: bool = False


@dataclass(frozen=True, slots=True)
class VoiceResult:
    response: InteractionResponse
    state: ConversationState
    metrics: VoicePipelineMetrics
    transcript: str | None = None


class VoiceInteractionService:
    """Orquestra canais; regras e mutações permanecem no pipeline existente."""

    def __init__(
        self,
        *,
        stt: STTProvider,
        interpreter: NaturalLanguageInterpreter,
        executor: InterpretationExecutor,
        dialogue: DialogueManager,
        states: StateService,
        tts: TTSProvider | None = None,
        status_listener: Callable[[ConversationState], None] | None = None,
    ) -> None:
        self.stt = stt
        self.interpreter = interpreter
        self.executor = executor
        self.dialogue = dialogue
        self.states = states
        self.tts = tts
        self.status_listener = status_listener
        self.confirmation_gate = ConfirmationGate()
        self._pending: InterpretationOutcome | None = None

    def process(self, audio: AudioInput) -> VoiceResult:
        total_started = perf_counter()
        self.dialogue.begin_listening()
        self._notify()
        stt_started = perf_counter()
        try:
            transcript = self.stt.transcribe(audio)
        except SpeechError:
            self.dialogue.fail()
            self._notify()
            response = InteractionResponse(
                "Não consegui entender o que você disse. A interface textual continua disponível.",
                priority=ResponsePriority.HIGH,
                requires_attention=True,
                speech_allowed=False,
            )
            return VoiceResult(
                response,
                self.dialogue.state,
                VoicePipelineMetrics(
                    stt_ms=self._elapsed(stt_started),
                    total_ms=self._elapsed(total_started),
                    stt_failed=True,
                ),
            )
        stt_ms = self._elapsed(stt_started)
        self.dialogue.begin_processing()
        self._notify()
        interpretation_started = perf_counter()
        outcome = self.interpreter.interpret(transcript, self.states.current())
        interpretation_ms = self._elapsed(interpretation_started)
        if outcome.disposition is InterpretationDisposition.CONFIRM:
            self._pending = outcome
            self.dialogue.wait_for_confirmation()
            self._notify()
            response = InteractionResponse(
                self._confirmation_text(outcome), requires_confirmation=True
            )
            tts_ms, tts_failed = self._speak(response)
            return VoiceResult(
                response,
                self.dialogue.state,
                VoicePipelineMetrics(
                    stt_ms, interpretation_ms, tts_ms=tts_ms,
                    total_ms=self._elapsed(total_started), tts_failed=tts_failed,
                ),
                transcript,
            )
        return self._complete(
            outcome, transcript, total_started, stt_ms, interpretation_ms
        )

    def confirm_text(self, text: str) -> VoiceResult:
        if (
            self.dialogue.state is not ConversationState.WAITING_CONFIRMATION
            or self._pending is None
        ):
            raise RuntimeError("Não existe confirmação de voz pendente.")
        normalized = text.strip().casefold()
        if normalized not in {"sim", "s", "não", "nao", "n", "cancela", "cancelar"}:
            response = InteractionResponse(
                "Responda sim, não ou cancela.", requires_confirmation=True
            )
            return VoiceResult(response, self.dialogue.state, VoicePipelineMetrics())
        confirmed = normalized in {"sim", "s"}
        outcome = self.confirmation_gate.resolve(self._pending, confirmed)
        self._pending = None
        return self._complete(outcome, text, perf_counter(), 0.0, 0.0)

    def confirm(self, audio: AudioInput) -> VoiceResult:
        """Transcreve somente sim/não/cancela; nunca consulta a IA novamente."""
        if self.dialogue.state is not ConversationState.WAITING_CONFIRMATION:
            raise RuntimeError("Não existe confirmação de voz pendente.")
        try:
            text = self.stt.transcribe(audio)
        except SpeechError:
            return VoiceResult(
                InteractionResponse(
                    "Não consegui ouvir a confirmação. Você também pode confirmar por texto.",
                    requires_confirmation=True,
                ),
                self.dialogue.state,
                VoicePipelineMetrics(stt_failed=True),
            )
        return self.confirm_text(text)

    def _complete(
        self,
        outcome: InterpretationOutcome,
        transcript: str,
        total_started: float,
        stt_ms: float,
        interpretation_ms: float,
    ) -> VoiceResult:
        core_started = perf_counter()
        if outcome.disposition is InterpretationDisposition.UNKNOWN:
            response = InteractionResponse(
                "Não consegui interpretar com segurança. Nenhuma ação foi feita."
            )
        else:
            response = self.executor.execute(outcome)
        core_ms = self._elapsed(core_started)
        self.dialogue.begin_responding()
        self._notify()
        tts_ms, tts_failed = self._speak(response)
        self.dialogue.finish_interaction()
        self._notify()
        return VoiceResult(
            response,
            self.dialogue.state,
            VoicePipelineMetrics(
                stt_ms, interpretation_ms, core_ms, tts_ms,
                self._elapsed(total_started), tts_failed=tts_failed,
            ),
            transcript,
        )

    def _speak(self, response: InteractionResponse) -> tuple[float, bool]:
        if self.tts is None or not response.speech_allowed:
            return 0.0, False
        started = perf_counter()
        try:
            self.tts.speak(response.text)
            return self._elapsed(started), False
        except SpeechError:
            return self._elapsed(started), True

    @staticmethod
    def _confirmation_text(outcome: InterpretationOutcome) -> str:
        entities = ", ".join(
            f"{key}={value}" for key, value in outcome.interpretation.entities
        )
        return f"Interpretei {outcome.interpretation.intent.value}: {entities}. Confirmar?"

    @staticmethod
    def _elapsed(started: float) -> float:
        return (perf_counter() - started) * 1000

    def _notify(self) -> None:
        if self.status_listener is not None:
            self.status_listener(self.dialogue.state)
