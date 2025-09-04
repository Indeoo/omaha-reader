from enum import Enum


class Street(Enum):
    """Poker street enumeration based on community cards count"""
    PREFLOP = "Preflop"
    FLOP = "Flop"
    TURN = "Turn"
    RIVER = "River"

    @classmethod
    def get_street_order(cls):
        return [Street.PREFLOP, Street.FLOP, Street.TURN, Street.RIVER]