from typing import List, Dict, Optional
from datetime import datetime
from collections import defaultdict

from src.core.domain.readed_card import ReadedCard
from src.core.domain.street import Street


class Game:

    def __init__(
            self,
            window_name: str,
            player_cards: List[ReadedCard] = None,
            table_cards: List[ReadedCard] = None,
            positions: Dict[int, str] = None,
            current_bids: Dict[int, float] = None,
            move_history: Dict[Street, List] = None
    ):
        self.window_name = window_name
        self.player_cards = player_cards or []
        self.table_cards = table_cards or []
        self.positions = positions or {}
        self.current_bids = current_bids or {}
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
            print(f"❌ Invalid table card count for street detection: {card_count} cards in {self.window_name}")
            return None

    def get_street_display(self) -> str:
        street = self.get_street()
        if street is None:
            return f"ERROR ({len(self.table_cards)} cards)"
        return street.value

    def add_moves(self, moves: List, street: Street):
        if moves:
            self.move_history[street].extend(moves)

    def reset_move_history(self):
        self.move_history = defaultdict(list)

    def reset_bids_for_new_street(self):
        self.current_bids = {}

    def get_moves_for_street(self, street: Street) -> List:
        return self.move_history.get(street, [])

    def get_all_moves(self) -> List:
        all_moves = []
        for street_moves in self.move_history.values():
            all_moves.extend(street_moves)
        return all_moves

    def get_player_cards_string(self) -> str:
        return ReadedCard.format_cards_simple(self.player_cards)

    def get_table_cards_string(self) -> str:
        return ReadedCard.format_cards_simple(self.table_cards)

    def get_positions_string(self) -> str:
        if not self.positions:
            return ""
        position_parts = []
        for player_num, position in sorted(self.positions.items()):
            player_label = "Main" if player_num == 1 else f"P{player_num}"
            position_parts.append(f"{player_label}:{position}")
        return ", ".join(position_parts)

    def get_moves_summary(self) -> str:
        if not self.move_history:
            return "No moves"

        total_moves = sum(len(moves) for moves in self.move_history.values())
        streets_with_moves = [street.value for street, moves in self.move_history.items() if moves]

        if streets_with_moves:
            return f"{total_moves} moves across {', '.join(streets_with_moves)}"
        return "No moves"

    def get_player_cards_for_web(self) -> List[Dict]:
        return self._format_cards_for_web(self.player_cards)

    def get_table_cards_for_web(self) -> List[Dict]:
        return self._format_cards_for_web(self.table_cards)

    def get_positions_for_web(self) -> List[Dict]:
        if not self.positions:
            return []

        formatted = []
        for player_num, position_name in sorted(self.positions.items()):
            formatted.append({
                'player': player_num,
                'player_label': 'Main' if player_num == 1 else f'Player {player_num}',
                'name': position_name,
                'is_main_player': player_num == 1
            })
        return formatted

    def get_moves_for_web(self) -> List[Dict]:
        moves_data = []
        for street, moves in self.move_history.items():
            for move in moves:
                moves_data.append({
                    'player_number': move.player_number,
                    'player_label': 'Main' if move.player_number == 1 else f'P{move.player_number}',
                    'action': move.action_type.value,
                    'amount': move.amount,
                    'total_contribution': move.total_pot_contribution,
                    'street': street.value
                })
        return moves_data

    def get_bids_for_web(self) -> List[Dict]:
        bids_data = []
        for player_num, bid_amount in sorted(self.current_bids.items()):
            if bid_amount > 0:
                bids_data.append({
                    'player_number': player_num,
                    'player_label': 'Main' if player_num == 1 else f'P{player_num}',
                    'amount': bid_amount
                })
        return bids_data

    def _format_cards_for_web(self, cards: List[ReadedCard]) -> List[Dict]:
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
        return bool(self.move_history and any(self.move_history.values()))

    def to_dict(self):
        return {
            'window_name': self.window_name,
            'player_cards': self.get_player_cards_for_web(),
            'table_cards': self.get_table_cards_for_web(),
            'positions': self.get_positions_for_web(),
            'moves': self.get_moves_for_web(),
            'bids': self.get_bids_for_web(),
            'player_cards_string': self.get_player_cards_string(),
            'table_cards_string': self.get_table_cards_string(),
            'positions_string': self.get_positions_string(),
            'moves_summary': self.get_moves_summary(),
            'street': self.get_street_display()
        }