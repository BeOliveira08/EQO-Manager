from dataclasses import dataclass
from time import perf_counter

from eqo.ai.context_builder import AIContextBuilder
from eqo.ai.interface import AIProvider
from eqo.ai.models import (
    AIInterpretation,
    AIMode,
    AIRequest,
    InterpretationDisposition,
    InterpretationOutcome,
)
from eqo.ai.ollama_provider import AIProviderTimeout, AIProviderUnavailable
from eqo.ai.policy import AIConfidencePolicy
from eqo.ai.validator import InvalidAIOutput
from eqo.domain.state import UserState
from eqo.interaction.command_parser import CommandParser
from eqo.interaction.intent import Intent, ParsedCommand


@dataclass(slots=True)
class AIMetrics:
    requests: int = 0
    unknown: int = 0
    confirmations: int = 0
    total_latency_ms: float = 0.0

    @property
    def average_latency_ms(self) -> float:
        return self.total_latency_ms / self.requests if self.requests else 0.0


class NaturalLanguageInterpreter:
    def __init__(
        self,
        *,
        mode: AIMode = AIMode.DISABLED,
        provider: AIProvider | None = None,
        parser: CommandParser | None = None,
        context_builder: AIContextBuilder | None = None,
        policy: AIConfidencePolicy | None = None,
    ) -> None:
        self.mode = mode
        self.provider = provider
        self.parser = parser or CommandParser()
        self.context_builder = context_builder or AIContextBuilder()
        self.policy = policy or AIConfidencePolicy()
        self.metrics = AIMetrics()

    def interpret(
        self, text: str, state: UserState | None = None
    ) -> InterpretationOutcome:
        explicit = self.parser.parse(text)
        if explicit.intent is not Intent.UNKNOWN:
            return InterpretationOutcome(
                InterpretationDisposition.ACCEPT,
                self._from_explicit(explicit),
            )
        if self.mode is AIMode.DISABLED or self.provider is None:
            return self._unknown("disabled")
        request = AIRequest(
            text=text,
            allowed_intents=tuple(Intent),
            context=self.context_builder.build(text, state),
        )
        started = perf_counter()
        self.metrics.requests += 1
        try:
            interpretation = self.provider.interpret(request)
            outcome = self.policy.evaluate(interpretation)
        except (InvalidAIOutput, AIProviderUnavailable, AIProviderTimeout):
            outcome = self._unknown("fallback")
        self.metrics.total_latency_ms += (perf_counter() - started) * 1000
        if outcome.disposition is InterpretationDisposition.UNKNOWN:
            self.metrics.unknown += 1
        elif outcome.disposition is InterpretationDisposition.CONFIRM:
            self.metrics.confirmations += 1
        return outcome

    @staticmethod
    def _from_explicit(command: ParsedCommand) -> AIInterpretation:
        value = command.arguments.get("value")
        entity_names = {
            Intent.CREATE_TASK: "title",
            Intent.COMPLETE_TASK: "task",
            Intent.DELETE_TASK: "task",
            Intent.CHANGE_NAME: "name",
            Intent.RECALL: "key",
            Intent.FORGET_MEMORY: "key",
        }
        entities: tuple[tuple[str, str], ...] = ()
        if value and command.intent in entity_names:
            entities = ((entity_names[command.intent], value),)
        elif value and command.intent is Intent.UPDATE_STATE and "=" in value:
            key, entity_value = value.split("=", 1)
            entities = ((key.strip(), entity_value.strip()),)
        elif value and command.intent in {Intent.REMEMBER, Intent.SET_PREFERENCE} and "=" in value:
            key, entity_value = value.split("=", 1)
            entities = (("key", key.strip()), ("value", entity_value.strip()))
        return AIInterpretation(
            command.intent, 1.0, entities, provider="deterministic", model="command_parser"
        )

    @staticmethod
    def _unknown(provider: str) -> InterpretationOutcome:
        return InterpretationOutcome(
            InterpretationDisposition.UNKNOWN,
            AIInterpretation(Intent.UNKNOWN, 0.0, provider=provider, model="none"),
        )
