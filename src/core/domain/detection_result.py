from typing import List, Dict, Any, Optional

from src.core.domain.readed_card import ReadedCard


class DetectionResult:

    def __init__(
            self,
            player_cards: Optional[List[ReadedCard]] = None,
            table_cards: Optional[List[ReadedCard]] = None,
            positions: Optional[List[Any]] = None,
            is_player_move: bool = False
    ):
        self.player_cards = player_cards or []
        self.table_cards = table_cards or []
        self.positions = positions or []
        self.is_player_move = is_player_move

    @staticmethod
    def builder():
        return DetectionResult.DetectionResultBuilder()

    @property
    def has_cards(self) -> bool:
        return bool(self.player_cards or self.table_cards)

    @property
    def has_positions(self) -> bool:
        return bool(self.positions)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'player_cards': self.player_cards,
            'table_cards': self.table_cards,
            'positions': self.positions,
            'has_cards': self.has_cards,
            'has_positions': self.has_positions,
            'is_player_move': self.is_player_move
        }

    def __repr__(self) -> str:
        player_count = len(self.player_cards)
        table_count = len(self.table_cards)
        position_count = len(self.positions)
        move_status = "MOVE" if self.is_player_move else "WAIT"
        return (f"DetectionResult("
                f"player_cards={player_count}, table_cards={table_count}, "
                f"positions={position_count}, status={move_status})")

    class DetectionResultBuilder:

        def __init__(self):
            self._player_cards: Optional[List[ReadedCard]] = None
            self._table_cards: Optional[List[ReadedCard]] = None
            self._positions: Optional[List[Any]] = None
            self._is_player_move: bool = False

        def with_player_cards(self, player_cards: List[ReadedCard]) -> 'DetectionResult.DetectionResultBuilder':
            self._player_cards = player_cards
            return self

        def with_table_cards(self, table_cards: List[ReadedCard]) -> 'DetectionResult.DetectionResultBuilder':
            self._table_cards = table_cards
            return self

        def with_positions(self, positions: List[Any]) -> 'DetectionResult.DetectionResultBuilder':
            self._positions = positions
            return self

        def with_player_move(self, is_player_move: bool = True) -> 'DetectionResult.DetectionResultBuilder':
            self._is_player_move = is_player_move
            return self

        def build(self) -> 'DetectionResult':
            return DetectionResult(
                player_cards=self._player_cards,
                table_cards=self._table_cards,
                positions=self._positions,
                is_player_move=self._is_player_move
            )