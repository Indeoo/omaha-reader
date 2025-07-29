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
            move_history: Dict[Street, List[Tuple[Position, MoveType]]] = None
    ):
        self.player_cards = player_cards or []
        self.table_cards = table_cards or []
        self.positions = positions or {}
        self.move_history = move_history or defaultdict(list)
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

    def get_player_cards_for_web(self) -> List[Dict]:
        return self._format_cards_for_web(self.player_cards)

    def get_table_cards_for_web(self) -> List[Dict]:
        return self._format_cards_for_web(self.table_cards)

    def get_positions_for_web(self) -> List[Dict]:
        if not self.positions:
            return []

        formatted = []
        for player_num, position  in enumerate(self.positions.values(), 1):
            formatted.append({
                'player': player_num,
                'player_label': f'Player {player_num}',
                'name': position.position_name,
                'is_main_player': player_num == 1
            })
        return formatted

    def get_moves_for_web(self) -> List[Dict]:
        if not self.move_history:
            return []

        moves_by_street = []

        # Position to player number mapping (1-indexed)
        position_to_player = {
            Position.BUTTON: 1,        # Hero position
            Position.SMALL_BLIND: 2,
            Position.BIG_BLIND: 3,
            Position.EARLY_POSITION: 4,
            Position.MIDDLE_POSITION: 5,
            Position.CUTOFF: 6
        }

        # Process streets in order: Preflop, Flop, Turn, River
        street_order = [Street.PREFLOP, Street.FLOP, Street.TURN, Street.RIVER]

        for street in street_order:
            moves = self.move_history.get(street, [])
            if moves:  # Only include streets that have moves
                street_moves = []
                for position, move_type in moves:
                    player_number = position_to_player.get(position, 1)  # Default to player 1
                    street_moves.append({
                        'player_number': player_number,
                        'player_label': f'P{player_number}',
                        'action': move_type.value,
                        'amount': 0.0,  # Not available in tuple format
                        'total_contribution': 0.0  # Not available in tuple format
                    })

                moves_by_street.append({
                    'street': street.value,
                    'moves': street_moves
                })

        return moves_by_street

    def _format_cards_for_web(self, cards: List[Detection]) -> List[Dict]:
        if not cards:
            return []

        formatted = []
        for card in cards:
            if card.template_name:
                formatted.append({
                    'name': card.template_name,
                    'display': card.format_with_unicode(),
                    'score': round(card.match_score, 3) if card.match_score else 0
                })
        return formatted

    def has_cards(self) -> bool:
        return bool(self.player_cards or self.table_cards)

    def has_positions(self) -> bool:
        return bool(self.positions)

    def has_moves(self) -> bool:
        return any(moves for moves in self.move_history.values())

    def get_player_cards_string(self) -> str:
        return format_cards_simple(self.player_cards)

    def get_table_cards_string(self) -> str:
        return format_cards_simple(self.table_cards)

    def get_solver_link_for_web(self) -> Optional[str]:
        from src.core.service.flophero_link_service import FlopHeroLinkService

        # Only generate link if we have meaningful data
        if not self.has_cards() and not self.has_moves():
            return None

        return FlopHeroLinkService.generate_link(self)

    def get_active_position(self):
        return {player_num: position for player_num, position in self.positions.items()
                if position.position_name != "NO"}

    def to_dict(self, window_name: str):
        return {
            'window_name': window_name,
            'player_cards_string': self.get_player_cards_string(),
            'table_cards_string': self.get_table_cards_string(),
            'player_cards': self.get_player_cards_for_web(),
            'table_cards': self.get_table_cards_for_web(),
            'positions': self.get_positions_for_web(),
            'moves': self.get_moves_for_web(),
            'street': self.get_street_display(),
            'solver_link': self.get_solver_link_for_web()
        }