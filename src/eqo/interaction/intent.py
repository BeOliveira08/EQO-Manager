from dataclasses import dataclass, field
from enum import StrEnum


class Intent(StrEnum):
    CREATE_TASK = "create_task"
    LIST_TASKS = "list_tasks"
    COMPLETE_TASK = "complete_task"
    DELETE_TASK = "delete_task"
    UPDATE_STATE = "update_state"
    GET_PLAN = "get_plan"
    SET_PREFERENCE = "set_preference"
    REMEMBER = "remember"
    RECALL = "recall"
    FORGET_MEMORY = "forget_memory"
    LIST_MEMORIES = "list_memories"
    CHANGE_NAME = "change_name"
    HELP = "help"
    EXIT = "exit"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ParsedCommand:
    intent: Intent
    arguments: dict[str, str] = field(default_factory=dict)
    raw_text: str = ""
