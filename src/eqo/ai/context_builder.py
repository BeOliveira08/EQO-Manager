from eqo.ai.models import AIContextFact
from eqo.domain.state import UserState
from eqo.services.memory_service import MemoryService


class AIContextBuilder:
    MAX_MEMORIES = 3

    def __init__(self, memories: MemoryService | None = None) -> None:
        self.memories = memories

    def build(self, query: str, state: UserState | None = None) -> tuple[AIContextFact, ...]:
        facts: list[AIContextFact] = []
        if state is not None:
            facts.extend([
                AIContextFact("current_state", "capacity", state.capacity.name),
                AIContextFact(
                    "current_state", "available_minutes", str(state.available_minutes)
                ),
            ])
        if self.memories is not None:
            for memory in self.memories.search(query)[:self.MAX_MEMORIES]:
                facts.append(AIContextFact("memory", memory.key, memory.value))
        return tuple(facts)

