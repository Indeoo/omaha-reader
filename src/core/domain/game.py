from typing import List, Dict, Optional, Tuple
from datetime import datetime
from collections import defaultdict

from src.core.domain.street import Street
from src.core.domain.detection import Detection
from src.core.domain.position import Position
from src.core.domain.moves import MoveType
from src.core.utils.card_format_utils import format_cards_simple


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


    def has_cards(self) -> bool:
        return bool(self.player_cards or self.table_cards)

    def has_positions(self) -> bool:
        return bool(self.positions)

    def has_moves(self) -> bool:
        return any(moves for moves in self.moves.values())

    def get_player_cards_string(self) -> str:
        return format_cards_simple(self.player_cards)

    def get_table_cards_string(self) -> str:
        return format_cards_simple(self.table_cards)

    def get_active_position(self):
        return {player_num: position for player_num, position in self.positions.items()
                if position.position_name != "NO"}