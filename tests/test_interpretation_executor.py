from pathlib import Path

from eqo.ai.models import (
    AIInterpretation,
    InterpretationDisposition,
    InterpretationOutcome,
)
from eqo.domain.state import Capacity
from eqo.interaction.intent import Intent
from eqo.services.interpretation_executor import InterpretationExecutor
from eqo.services.memory_service import MemoryService
from eqo.services.state_service import StateService
from eqo.services.task_service import TaskService
from eqo.storage.sqlite_memory_repository import SQLiteMemoryRepository
from eqo.storage.sqlite_repository import SQLiteTaskRepository
from eqo.storage.sqlite_state_repository import SQLiteUserStateRepository


def make_executor(tmp_path: Path) -> tuple[InterpretationExecutor, StateService]:
    database = tmp_path / "eqo.db"
    states = StateService(SQLiteUserStateRepository(database))
    return InterpretationExecutor(
        tasks=TaskService(SQLiteTaskRepository(database)),
        states=states,
        memories=MemoryService(SQLiteMemoryRepository(database)),
    ), states


def state_outcome(disposition: InterpretationDisposition) -> InterpretationOutcome:
    return InterpretationOutcome(
        disposition,
        AIInterpretation(
            Intent.UPDATE_STATE, 0.7, (("capacity", "LOW"),), "fake", "tiny"
        ),
    )


def test_executor_refuses_unconfirmed_interpretation_without_mutation(tmp_path: Path) -> None:
    executor, states = make_executor(tmp_path)
    response = executor.execute(state_outcome(InterpretationDisposition.CONFIRM))
    assert "nenhuma ação" in response.text
    assert states.current().capacity is Capacity.MEDIUM


def test_executor_applies_only_accepted_structured_state(tmp_path: Path) -> None:
    executor, states = make_executor(tmp_path)
    response = executor.execute(state_outcome(InterpretationDisposition.ACCEPT))
    assert "Estado atualizado" in response.text
    assert states.current().capacity is Capacity.LOW
