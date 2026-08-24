from dataclasses import dataclass
from enum import StrEnum


class Decision(StrEnum):
    EXECUTE = "execute"
    DEFER = "defer"
    REDUCE = "reduce"
    SPLIT = "split"
    REORDER = "reorder"
    CANCEL = "cancel"
    REMIND = "remind"
    REST = "rest"
    ASK_USER = "ask_user"
    CONSIDER = "consider"


@dataclass(frozen=True, slots=True)
class DecisionResult:
    decision: Decision
    reason: str

