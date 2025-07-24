from enum import Enum


class ActionType(Enum):
    FOLD = "fold"
    CALL = "call"
    RAISE = "raise"
    CHECK = "check"
    SMALL_BLIND = "sb"
    BIG_BLIND = "bb"
