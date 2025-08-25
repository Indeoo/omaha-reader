from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple

from .detection import Detection
from .moves import MoveType
from .position import Position
from .street import Street


class GameSnapshot:

    def __init__(
            self,
            player_cards: Optional[List[Detection]] = None,
            table_cards: Optional[List[Detection]] = None,
            positions: Optional[Dict[int, Detection]] = None,
            bids: Optional[List[Any]] = None,
            is_player_move: bool = False,
            actions: Optional[Dict[int, Detection]] = None,
            moves: Optional[Dict[Street, List[Tuple[Position, MoveType]]]] = None
    ):
        self.player_cards = player_cards or []
        self.table_cards = table_cards or []
        self.positions = positions or {}
        self.bids = bids or {}
        self.is_player_move = is_player_move
        self.actions = actions or {}
        self.moves = moves or defaultdict(list)

    @staticmethod
    def builder():
        return GameSnapshot.Builder()

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

    class Builder:

        def __init__(self):
            self._player_cards: Optional[List[Detection]] = None
            self._table_cards: Optional[List[Detection]] = None
            self._positions: Optional[Dict[int, Detection]] = None
            self._bids: Optional[List[Any]] = None
            self._is_player_move: bool = False
            self._actions: Optional[Dict[int, Detection]] = None
            self._moves: Optional[Dict[Street, List[Tuple[Position, MoveType]]]] = None

        def with_player_cards(self, player_cards: List[Detection]) -> 'GameSnapshot.Builder':
            self._player_cards = player_cards
            return self

        def with_table_cards(self, table_cards: List[Detection]) -> 'GameSnapshot.Builder':
            self._table_cards = table_cards
            return self

        def with_positions(self, positions: Dict[int, Detection]) -> 'GameSnapshot.Builder':
            self._positions = positions
            return self

        def with_bids(self, bids: List[Any]) -> 'GameSnapshot.Builder':
            self._bids = bids
            return self

        def with_player_move(self, is_player_move: bool = True) -> 'GameSnapshot.Builder':
            self._is_player_move = is_player_move
            return self

        def with_actions(self, actions: bool = True) -> 'GameSnapshot.Builder':
            self._actions = actions
            return self

        def with_moves(self, moves: Dict[Street, List[Tuple[Position, MoveType]]]) -> 'GameSnapshot.Builder':
            self._moves = moves
            return self

        def build(self) -> 'GameSnapshot':
            return GameSnapshot(
                player_cards=self._player_cards,
                table_cards=self._table_cards,
                positions=self._positions,
                bids=self._bids,
                is_player_move=self._is_player_move,
                actions=self._actions,
                moves=self._moves
            )