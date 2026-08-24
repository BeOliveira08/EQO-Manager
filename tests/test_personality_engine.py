from dataclasses import replace
from datetime import UTC, datetime

import pytest

from eqo.domain.decision import Decision, DecisionResult
from eqo.domain.persona import AutonomyLevel, Persona
from eqo.domain.plan import Plan, PlanItem, PlanItemKind
from eqo.domain.user import UserProfile
from eqo.services.personality_engine import PersonalityEngine


def test_decision_response_preserves_action_and_exact_reason() -> None:
    result = DecisionResult(Decision.DEFER, "Esforço alto e tarefa flexível.")
    response = PersonalityEngine().respond_to_decision(
        result, Persona(name="Alfred"), UserProfile("Bernardo", "Alfred")
    )
    assert response.decision is Decision.DEFER
    assert response.reason == result.reason
    assert response.text.startswith("Bernardo")


def test_confirm_autonomy_requests_confirmation_without_changing_decision() -> None:
    result = DecisionResult(Decision.REDUCE, "Capacidade baixa.")
    persona = replace(Persona(), autonomy=AutonomyLevel.CONFIRM)
    response = PersonalityEngine().respond_to_decision(result, persona)
    assert response.decision is Decision.REDUCE
    assert response.requires_confirmation is True


def test_explanation_is_derived_from_core_reason() -> None:
    result = DecisionResult(Decision.SPLIT, "Não cabe no tempo disponível.")
    response = PersonalityEngine().explain(result, Persona(name="EQO"))
    assert result.reason in response.text
    assert response.reason == result.reason


def test_plan_summary_uses_operational_plan_facts() -> None:
    now = datetime(2026, 8, 24, 14, tzinfo=UTC)
    plan = Plan(now, 60, (
        PlanItem(
            PlanItemKind.TASK, "Estudar", Decision.SPLIT, "Tempo curto.",
            30, remaining_minutes=30, task_id="1", starts_at=now, segments=(30,),
        ),
        PlanItem(
            PlanItemKind.TASK, "Limpar", Decision.DEFER, "Pode esperar.",
            0, remaining_minutes=30, task_id="2",
        ),
    ))
    response = PersonalityEngine().describe_plan(plan, Persona(), UserProfile("Bernardo"))
    assert "30 minutos" in response.text
    assert "1 em blocos menores" in response.text
    assert "1 para depois" in response.text


def test_decision_response_without_reason_is_rejected() -> None:
    from eqo.interaction.response import InteractionResponse

    with pytest.raises(ValueError, match="justificativa"):
        InteractionResponse("Texto", decision=Decision.EXECUTE)


def test_proactivity_respects_passive_level_and_requires_opt_in() -> None:
    engine = PersonalityEngine()
    assert engine.proactive_for_free_time(
        60, replace(Persona(), autonomy=AutonomyLevel.PASSIVE)
    ) is None
    message = engine.proactive_for_free_time(60, Persona())
    assert message is not None
    assert message.requires_confirmation is True
