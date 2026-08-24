from datetime import date

from eqo.ai.models import InterpretationDisposition, InterpretationOutcome
from eqo.domain.memory import MemoryImportance, MemorySource
from eqo.domain.state import Capacity
from eqo.domain.task import Priority, Task
from eqo.interaction.intent import Intent
from eqo.interaction.response import InteractionResponse
from eqo.services.context_engine import ContextEngine
from eqo.services.memory_service import MemoryService
from eqo.services.planner import Planner
from eqo.services.profile_service import ProfileService
from eqo.services.state_service import StateService
from eqo.services.task_service import TaskService


class InterpretationExecutor:
    """Única ponte entre uma interpretação aceita e serviços determinísticos."""

    def __init__(
        self,
        *,
        tasks: TaskService,
        states: StateService,
        memories: MemoryService,
        profiles: ProfileService | None = None,
        planner: Planner | None = None,
        context_engine: ContextEngine | None = None,
    ) -> None:
        self.tasks = tasks
        self.states = states
        self.memories = memories
        self.profiles = profiles
        self.planner = planner
        self.context_engine = context_engine

    def execute(self, outcome: InterpretationOutcome) -> InteractionResponse:
        if outcome.disposition is not InterpretationDisposition.ACCEPT:
            return InteractionResponse(
                "A interpretação ainda não foi aceita; nenhuma ação foi executada."
            )
        interpretation = outcome.interpretation
        entities = dict(interpretation.entities)
        intent = interpretation.intent
        if intent is Intent.UPDATE_STATE:
            state = self.states.update(
                capacity=(Capacity[entities["capacity"].upper()]
                          if "capacity" in entities else None),
                energy=self._integer(entities, "energy"),
                focus=self._integer(entities, "focus"),
                stress=self._integer(entities, "stress"),
                available_minutes=self._integer(entities, "available_minutes"),
            )
            return InteractionResponse(
                f"Estado atualizado. Capacidade: {state.capacity.name}.", intent=intent
            )
        if intent in {Intent.REMEMBER, Intent.SET_PREFERENCE}:
            memory = self.memories.remember(
                entities["key"],
                entities["value"],
                importance=MemoryImportance.HIGH,
                source=MemorySource.USER_EXPLICIT,
            )
            return InteractionResponse(f"Vou lembrar: {memory.value}", intent=intent)
        if intent is Intent.FORGET_MEMORY:
            deleted = self.memories.forget(entities["key"])
            text = "Memória apagada." if deleted else "Memória não encontrada."
            return InteractionResponse(text, intent=intent)
        if intent is Intent.CHANGE_NAME and self.profiles is not None:
            profile = self.profiles.change_assistant_name(entities["name"])
            return InteractionResponse(
                f"A partir de agora sou {profile.assistant_name}.", intent=intent
            )
        if intent is Intent.CREATE_TASK:
            created_task = self.tasks.create(
                entities["title"],
                self._priority(entities.get("priority")),
                date.fromisoformat(entities["deadline"]) if entities.get("deadline") else None,
                estimated_minutes=self._integer(entities, "estimated_minutes"),
                effort=self._integer(entities, "effort") or 3,
                flexibility=self._integer(entities, "flexibility") or 3,
            )
            return InteractionResponse(f"Tarefa criada: {created_task.title}.", intent=intent)
        if intent in {Intent.COMPLETE_TASK, Intent.DELETE_TASK}:
            target_task = self._find_task(entities["task"])
            if target_task is None:
                return InteractionResponse("Tarefa não encontrada.", intent=intent)
            if intent is Intent.COMPLETE_TASK:
                self.tasks.complete(target_task.id)
                return InteractionResponse("Tarefa concluída.", intent=intent)
            self.tasks.remove(target_task.id)
            return InteractionResponse("Tarefa removida.", intent=intent)
        if intent is Intent.LIST_TASKS:
            return InteractionResponse(
                f"Você possui {len(self.tasks.list())} tarefa(s).", intent=intent
            )
        if intent in {Intent.LIST_MEMORIES, Intent.RECALL}:
            memories = (
                self.memories.search(entities.get("query") or entities.get("key", ""))
                if entities else self.memories.list()
            )
            return InteractionResponse(
                f"Encontrei {len(memories)} memória(s).", intent=intent
            )
        if intent is Intent.GET_PLAN and self.planner and self.context_engine:
            state = self.states.current()
            context = self.context_engine.current(state)
            plan = self.planner.create_plan(self.tasks.list(), state, context)
            return InteractionResponse(
                f"Plano preparado com {plan.allocated_minutes} minutos.", intent=intent
            )
        if intent is Intent.HELP:
            return InteractionResponse("Posso cuidar de tarefas, estado, plano e memória.")
        return InteractionResponse("A intent é válida, mas ainda não possui executor seguro.")

    def _find_task(self, title: str) -> Task | None:
        normalized = title.casefold().strip()
        return next((task for task in self.tasks.list()
                     if task.title.casefold() == normalized), None)

    @staticmethod
    def _integer(entities: dict[str, str], key: str) -> int | None:
        return int(entities[key]) if key in entities else None

    @staticmethod
    def _priority(value: str | None) -> Priority:
        if value is None:
            return Priority.MEDIUM
        names = {"HIGH": Priority.HIGH, "MEDIUM": Priority.MEDIUM, "LOW": Priority.LOW}
        if value.upper() in names:
            return names[value.upper()]
        return Priority(int(value))
