from typing import List, Tuple, Dict

from shared.domain.moves import MoveType
from table_detector.domain.omaha_game import OmahaGame
from shared.domain.position import Position
from shared.domain.street import Street


def group_moves_by_street(player_moves: Dict[Position, List[MoveType]]) -> Dict[Street, List[Tuple[Position, MoveType]]]:
    if not player_moves:
        return {Street.PREFLOP: [], Street.FLOP: [], Street.TURN: [], Street.RIVER: []}

    game = OmahaGame(player_moves.keys())
    execute_game(game, player_moves)

    return game.get_moves_by_street()


def execute_game(game, player_moves):
    index_to_pos_work = game.get_seat_to_position_mapping()

    while any(player_moves[pos] for pos in player_moves):
        current_position = index_to_pos_work[game.poker_state.actor_index]
        move = player_moves[current_position].pop(0)
        game.process_action(current_position, move)
