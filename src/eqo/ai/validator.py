import json
from collections.abc import Mapping
from datetime import date
from typing import Any

from eqo.ai.models import AIInterpretation, AIRequest
from eqo.interaction.intent import Intent


class InvalidAIOutput(ValueError):
    pass


class AIOutputValidator:
    MAX_OUTPUT_CHARS = 8_000
    MAX_ENTITY_CHARS = 500
    ALLOWED_ENTITIES = {
        Intent.CREATE_TASK: {
            "title", "deadline", "priority", "estimated_minutes", "effort", "flexibility"
        },
        Intent.LIST_TASKS: {"filter", "date"},
        Intent.COMPLETE_TASK: {"task"},
        Intent.DELETE_TASK: {"task"},
        Intent.UPDATE_STATE: {
            "capacity", "energy", "focus", "stress", "available_minutes"
        },
        Intent.GET_PLAN: set(),
        Intent.SET_PREFERENCE: {"key", "value"},
        Intent.REMEMBER: {"key", "value"},
        Intent.RECALL: {"key", "query"},
        Intent.FORGET_MEMORY: {"key"},
        Intent.LIST_MEMORIES: set(),
        Intent.CHANGE_NAME: {"name"},
        Intent.HELP: set(),
        Intent.EXIT: set(),
        Intent.UNKNOWN: set(),
    }
    REQUIRED_ANY = {
        Intent.UPDATE_STATE: {"capacity", "energy", "focus", "stress", "available_minutes"},
    }
    REQUIRED = {
        Intent.CREATE_TASK: {"title"},
        Intent.COMPLETE_TASK: {"task"},
        Intent.DELETE_TASK: {"task"},
        Intent.SET_PREFERENCE: {"key", "value"},
        Intent.REMEMBER: {"key", "value"},
        Intent.FORGET_MEMORY: {"key"},
        Intent.CHANGE_NAME: {"name"},
    }

    def parse_and_validate(
        self,
        raw_output: str,
        request: AIRequest,
        *,
        provider: str,
        model: str,
    ) -> AIInterpretation:
        if len(raw_output) > self.MAX_OUTPUT_CHARS:
            raise InvalidAIOutput("A saída do modelo excede o limite permitido.")
        try:
            payload = json.loads(raw_output)
        except json.JSONDecodeError as error:
            raise InvalidAIOutput("O modelo não retornou JSON válido.") from error
        if not isinstance(payload, Mapping):
            raise InvalidAIOutput("A saída deve ser um objeto JSON.")
        return self.validate(payload, request, provider=provider, model=model)

    def validate(
        self,
        payload: Mapping[str, Any],
        request: AIRequest,
        *,
        provider: str,
        model: str,
    ) -> AIInterpretation:
        try:
            intent = Intent(payload["intent"])
        except (KeyError, ValueError, TypeError) as error:
            raise InvalidAIOutput("Intent ausente ou não permitida.") from error
        if intent not in request.allowed_intents:
            raise InvalidAIOutput("A intent não está autorizada para esta requisição.")
        confidence = payload.get("confidence")
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
            raise InvalidAIOutput("Confidence deve ser um número entre 0 e 1.")
        if not 0.0 <= float(confidence) <= 1.0:
            raise InvalidAIOutput("Confidence deve estar entre 0 e 1.")
        raw_entities = payload.get("entities", {})
        if not isinstance(raw_entities, Mapping):
            raise InvalidAIOutput("Entities deve ser um objeto JSON.")
        allowed = self.ALLOWED_ENTITIES[intent]
        if not set(raw_entities).issubset(allowed):
            raise InvalidAIOutput("A saída contém entidades não permitidas para a intent.")
        required = self.REQUIRED.get(intent, set())
        if not required.issubset(raw_entities):
            raise InvalidAIOutput("A saída não contém todas as entidades obrigatórias.")
        required_any = self.REQUIRED_ANY.get(intent)
        if required_any is not None and not required_any.intersection(raw_entities):
            raise InvalidAIOutput("A intent exige ao menos uma entidade de estado.")
        entities: list[tuple[str, str]] = []
        for key, value in raw_entities.items():
            if (
                not isinstance(key, str)
                or isinstance(value, bool)
                or not isinstance(value, (str, int, float))
            ):
                raise InvalidAIOutput("Entidades devem possuir valores escalares.")
            normalized = str(value).strip()
            if not normalized or len(normalized) > self.MAX_ENTITY_CHARS:
                raise InvalidAIOutput("Uma entidade está vazia ou excede o limite.")
            entities.append((key, normalized))
        self._validate_entity_values(intent, dict(entities))
        return AIInterpretation(
            intent=intent,
            confidence=float(confidence),
            entities=tuple(entities),
            provider=provider,
            model=model,
        )

    @staticmethod
    def _validate_entity_values(intent: Intent, entities: dict[str, str]) -> None:
        if "capacity" in entities and entities["capacity"].upper() not in {
            "VERY_LOW", "LOW", "MEDIUM", "HIGH", "VERY_HIGH"
        }:
            raise InvalidAIOutput("Capacity possui valor inválido.")
        for key in {"energy", "focus", "stress", "effort", "flexibility"} & entities.keys():
            try:
                value = int(entities[key])
            except ValueError as error:
                raise InvalidAIOutput(f"{key} deve ser inteiro.") from error
            if not 1 <= value <= 5:
                raise InvalidAIOutput(f"{key} deve estar entre 1 e 5.")
        if "available_minutes" in entities or "estimated_minutes" in entities:
            for key in {"available_minutes", "estimated_minutes"} & entities.keys():
                try:
                    minimum = 1 if key == "estimated_minutes" else 0
                    if int(entities[key]) < minimum:
                        raise ValueError
                except ValueError as error:
                    raise InvalidAIOutput(f"{key} deve ser inteiro não negativo.") from error
        if intent is Intent.UNKNOWN and entities:
            raise InvalidAIOutput("UNKNOWN não pode carregar entidades.")
        if "priority" in entities and entities["priority"].upper() not in {
            "HIGH", "MEDIUM", "LOW", "1", "2", "3"
        }:
            raise InvalidAIOutput("Priority possui valor inválido.")
        if "deadline" in entities:
            try:
                date.fromisoformat(entities["deadline"])
            except ValueError as error:
                raise InvalidAIOutput("Deadline deve usar o formato YYYY-MM-DD.") from error
