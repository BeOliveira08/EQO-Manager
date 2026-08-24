from eqo.domain.decision import Decision, DecisionResult
from eqo.domain.persona import AutonomyLevel, Persona
from eqo.domain.plan import Plan, PlanItemKind
from eqo.domain.user import UserProfile
from eqo.interaction.intent import Intent
from eqo.interaction.response import InteractionResponse, ProactiveMessage


class PersonalityEngine:
    """Apresenta fatos do Core sem criar ou substituir decisões."""

    TEMPLATES = {
        Decision.EXECUTE: "esta tarefa precisa de atenção agora.",
        Decision.DEFER: "isso pode esperar e ficará mais leve para depois.",
        Decision.REDUCE: "vou sugerir uma versão menor desta tarefa.",
        Decision.SPLIT: "vale dividir esta tarefa em blocos menores.",
        Decision.REST: "uma pausa agora ajudará a proteger sua capacidade.",
        Decision.CANCEL: "esta tarefa já não exige uma ação.",
        Decision.CONSIDER: "esta tarefa pode entrar no seu plano atual.",
        Decision.REORDER: "esta tarefa deve mudar de posição no plano.",
        Decision.REMIND: "é melhor manter um lembrete para esta tarefa.",
        Decision.ASK_USER: "preciso da sua confirmação antes de continuar.",
    }

    def respond_to_decision(
        self,
        result: DecisionResult,
        persona: Persona,
        profile: UserProfile | None = None,
    ) -> InteractionResponse:
        message = self.TEMPLATES[result.decision]
        text = f"{profile.name}, {message}" if profile else message.capitalize()
        return InteractionResponse(
            text=text,
            decision=result.decision,
            reason=result.reason,
            requires_confirmation=self._requires_confirmation(result.decision, persona),
        )

    def explain(
        self, result: DecisionResult, persona: Persona
    ) -> InteractionResponse:
        return InteractionResponse(
            text=f"{persona.name}: {result.reason}",
            decision=result.decision,
            reason=result.reason,
            requires_confirmation=False,
        )

    def describe_plan(
        self, plan: Plan, persona: Persona, profile: UserProfile | None = None
    ) -> InteractionResponse:
        tasks = [item for item in plan.items if item.kind is PlanItemKind.TASK]
        deferred = sum(item.deferred for item in tasks)
        split_or_reduced = sum(
            item.decision in {Decision.SPLIT, Decision.REDUCE} for item in tasks
        )
        greeting = f"{profile.name}, " if profile else ""
        text = (
            f"{greeting}preparei um plano de {plan.allocated_minutes} minutos. "
            f"Há {len(tasks)} tarefa(s), {split_or_reduced} em blocos menores "
            f"e {deferred} para depois."
        )
        return InteractionResponse(text=text, intent=Intent.GET_PLAN)

    def proactive_for_free_time(
        self, available_minutes: int, persona: Persona
    ) -> ProactiveMessage | None:
        if available_minutes < 30 or persona.autonomy is AutonomyLevel.PASSIVE:
            return None
        return ProactiveMessage(
            text=(
                f"Você tem {available_minutes} minutos livres. "
                "Quer que eu veja o que cabe nesse período?"
            ),
            trigger="available_time",
            requires_confirmation=True,
        )

    @staticmethod
    def _requires_confirmation(decision: Decision, persona: Persona) -> bool:
        return (
            persona.autonomy is AutonomyLevel.CONFIRM
            and decision not in {Decision.CONSIDER, Decision.ASK_USER}
        )
