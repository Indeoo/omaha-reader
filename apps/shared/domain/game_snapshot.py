from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple

from shared.domain.detection import Detection
from shared.domain.moves import MoveType
from shared.domain.position import Position
from shared.domain.street import Street


class GameSnapshot:

    def __init__(
            self,
            player_cards: Optional[List[Detection]] = None,
            table_cards: Optional[List[Detection]] = None,
            positions: Optional[Dict[int, Detection]] = None,
            bids: Optional[List[Any]] = None,
            is_player_move: bool = False,
            actions: Optional[Dict[int, List[Detection]]] = None,
            moves: Optional[Dict[Street, List[Tuple[Position, MoveType]]]] = None
    ):
        self.player_cards = player_cards or []
        self.table_cards = table_cards or []
        self.positions = positions or {}
        self.bids = bids or {}
        self.is_player_move = is_player_move
        self.actions = actions or {}
        self.moves = moves or defaultdict(list)

    @property
    def has_cards(self) -> bool:
        return bool(self.player_cards or self.table_cards)

    @property
    def has_positions(self) -> bool:
        return bool(self.positions)

    @property
    def has_bids(self) -> bool:
        return bool(self.bids)

    @property
    def has_moves(self) -> bool:
        return any(moves for moves in self.moves.values())

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

    def get_active_position(self):
        return {player_num: position for player_num, position in self.positions.items()
                if position.name != "NO"}

    def get_street_display(self) -> str:
        street = self.get_street()
        if street is None:
            return f"ERROR ({len(self.table_cards)} cards)"
        return street.value

    def to_game_update_message(
        self,
        client_id: str,
        window_name: str,
        detection_interval: int
    ):
        """Convert GameSnapshot directly to GameUpdateMessage protocol format."""
        from shared.protocol.message_protocol import GameUpdateMessage
        from shared.utils.card_format_utils import format_cards_simple
        from datetime import datetime
        from table_detector.services.flophero_link_service import FlopHeroLinkService

        return GameUpdateMessage(
            type='game_update',
            client_id=client_id,
            window_name=window_name,
            timestamp=datetime.now().isoformat(),
            game_data={
                'player_cards_string': format_cards_simple(self.player_cards),
                'player_cards': [
                    {'name': c.template_name, 'display': c.format_with_unicode(), 'score': round(c.match_score, 3)}
                    for c in self.player_cards
                ],
                'table_cards_string': format_cards_simple(self.table_cards),
                'table_cards': [
                    {'name': c.template_name, 'display': c.format_with_unicode(), 'score': round(c.match_score, 3)}
                    for c in self.table_cards
                ],
                'positions': [
                    {'player': i+1, 'player_label': f'Player {i+1}', 'name': p.template_name, 'is_main_player': i==0}
                    for i, p in enumerate(self.positions.values())
                ],
                'moves': self._format_moves_for_protocol(),
                'street': self.get_street_display(),
                'solver_link': FlopHeroLinkService.generate_link(self)
            },
            detection_interval=detection_interval
        )

    def _format_moves_for_protocol(self):
        """Format moves dictionary for protocol transmission."""
        if not self.moves:
            return []

        moves_by_street = []
        for street, moves in self.moves.items():
            street_moves = []
            for position, move_type in moves:
                street_moves.append({
                    'player_label': position.name,
                    'action': move_type.value
                })

            moves_by_street.append({
                'street': street.value,
                'moves': street_moves
            })

        return moves_by_street

    def __repr__(self) -> str:
        player_count = len(self.player_cards)
        table_count = len(self.table_cards)
        position_count = len(self.positions)
        bid_count = len(self.bids)
        moves_count = sum(len(moves) for moves in self.moves.values())
        move_status = "MOVE" if self.is_player_move else "WAIT"
        return (f"DetectionResult("
                f"player_cards={player_count}, table_cards={table_count}, "
                f"positions={position_count}, bids={bid_count}, moves={moves_count}, status={move_status})")