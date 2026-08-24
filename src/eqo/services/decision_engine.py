from datetime import date

from eqo.domain.decision import Decision, DecisionResult
from eqo.domain.state import Capacity, UserState
from eqo.domain.task import Task

__all__ = ["Decision", "DecisionEngine", "DecisionResult"]


class DecisionEngine:
    """Regras explícitas e auditáveis; nenhum modelo de IA é necessário."""

    def evaluate(
        self, task: Task, state: UserState, today: date | None = None
    ) -> DecisionResult:
        current_date = today or date.today()
        if task.completed:
            return DecisionResult(Decision.CANCEL, "A tarefa já está concluída.")
        if task.deadline is not None and task.deadline <= current_date:
            return DecisionResult(Decision.EXECUTE, "O prazo chegou ou já passou.")
        if state.capacity is Capacity.VERY_LOW and state.stress >= 4:
            return DecisionResult(Decision.REST, "Capacidade muito baixa e estresse alto.")
        if (
            task.estimated_minutes is not None
            and state.available_minutes > 0
            and task.estimated_minutes > state.available_minutes
        ):
            return DecisionResult(Decision.SPLIT, "A tarefa não cabe no tempo disponível.")
        if state.capacity <= Capacity.LOW and task.effort >= 4:
            if task.flexibility >= 4:
                return DecisionResult(Decision.DEFER, "Esforço alto e tarefa flexível.")
            return DecisionResult(Decision.REDUCE, "Esforço alto e pouca flexibilidade.")
        if (
            state.capacity <= Capacity.LOW
            and task.effort <= 2
            and task.flexibility <= 2
        ):
            return DecisionResult(Decision.EXECUTE, "Tarefa leve e pouco flexível.")
        if state.focus <= 2 and task.effort >= 3:
            return DecisionResult(Decision.REDUCE, "Foco baixo para o esforço exigido.")
        return DecisionResult(Decision.CONSIDER, "Nenhuma regra exige intervenção.")

    def recommend(self, task: Task, state: UserState) -> Decision:
        """Compatibilidade com a API v0.1; prefira ``evaluate`` para auditoria."""
        return self.evaluate(task, state).decision
