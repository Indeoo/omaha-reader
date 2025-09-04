from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from apps.shared.domain.detection import Detection
from apps.shared.domain.moves import MoveType
from apps.shared.domain.position import Position
from apps.shared.domain.street import Street


class Game:

    def __init__(
            self,
            player_cards: List[Detection] = None,
            table_cards: List[Detection] = None,
            positions: Dict[int, Detection] = None,
            moves: Dict[Street, List[Tuple[Position, MoveType]]] = None
    ):
        self.player_cards = player_cards or []
        self.table_cards = table_cards or []
        self.positions = positions or {}
        self.moves = moves or defaultdict(list)
        self.timestamp = datetime.now()

    def get_street(self) -> Optional[Street]:
        card_count = len(self.table_cards)

        if card_count == 0:
            return Street.PREFLOP
        elif card_count == 3:
            return Street.FLOP
        elif card_count == 4:
            return Street.TURN
        elif card_count == 5:
            return Street.RIVER
        else:
            return None

    def get_street_display(self) -> str:
        street = self.get_street()
        if street is None:
            return f"ERROR ({len(self.table_cards)} cards)"
        return street.value

    def get_active_position(self):
        return {player_num: position for player_num, position in self.positions.items()
                if position.name != "NO"}

    def get_moves_by_streets(self) -> List[Tuple[Street, List[Tuple[Position, MoveType]]]]:
        """Returns moves organized by street in chronological order.
        Only includes streets that have moves."""
        street_moves = []
        for street in Street.get_street_order():
            moves = self.moves.get(street, [])
            if moves:
                street_moves.append((street, moves))
        return street_moves