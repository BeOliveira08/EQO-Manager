from eqo.domain.event import EventType
from eqo.domain.memory import Memory, MemoryImportance, MemorySource, MemoryType
from eqo.storage.repositories import EventRepository, MemoryRepository


class MemoryConsolidator:
    """Consolida somente padrões com regra explícita e evidência mínima."""

    MINIMUM_STUDY_EVENTS = 3

    def __init__(self, memories: MemoryRepository, events: EventRepository) -> None:
        self.memories = memories
        self.events = events

    def consolidate_study_time(self) -> Memory | None:
        sessions = self.events.list(EventType.STUDY_SESSION)
        if len(sessions) < self.MINIMUM_STUDY_EVENTS:
            return None
        periods = [
            self._period(int(event.attribute("hour") or event.occurred_at.hour))
            for event in sessions
        ]
        counts = {period: periods.count(period) for period in set(periods)}
        preferred, occurrences = max(counts.items(), key=lambda item: (item[1], item[0]))
        confidence = occurrences / len(periods)
        if confidence < 0.6:
            return None
        return self.memories.upsert(Memory(
            key="preferred_study_time",
            value=preferred,
            memory_type=MemoryType.SEMANTIC,
            importance=MemoryImportance.MEDIUM,
            confidence=round(confidence, 2),
            source=MemorySource.INFERRED,
        ))

    @staticmethod
    def _period(hour: int) -> str:
        if 5 <= hour < 12:
            return "morning"
        if 12 <= hour < 18:
            return "afternoon"
        if 18 <= hour < 24:
            return "evening"
        return "night"
