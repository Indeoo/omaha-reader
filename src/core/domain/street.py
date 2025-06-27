from enum import Enum


class Street(Enum):
    """Poker street enumeration based on community cards count"""
    PREFLOP = "Preflop"
    FLOP = "Flop"
    TURN = "Turn"
    RIVER = "River"