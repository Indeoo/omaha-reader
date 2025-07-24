from collections import defaultdict
from typing import List, Union, Tuple, Dict


def group_moves_by_street(player_moves: Dict[str, List[Union[str, Tuple[str, float]]]]) -> Dict[str, List[str]]:
    street_moves = defaultdict(list)

    all_moves_ordered = []

    max_rounds = max(len(moves) for moves in player_moves.values()) if player_moves else 0

    position_order = ['SB', 'BB', 'UTG', 'MP', 'CO', 'BTN']

    for round_idx in range(max_rounds):
        for position in position_order:
            if position in player_moves and round_idx < len(player_moves[position]):
                move = player_moves[position][round_idx]
                if isinstance(move, tuple):
                    move = move[0]
                all_moves_ordered.append(move)

    current_street = "preflop"
    betting_round = 0
    moves_in_current_round = 0
    active_players = len([p for p, moves in player_moves.items() if moves and moves[0] != "fold"])

    for i, move in enumerate(all_moves_ordered):
        street_moves[current_street].append(move)
        moves_in_current_round += 1

        if moves_in_current_round >= active_players:
            if betting_round == 0 and current_street == "preflop":
                current_street = "flop"
                betting_round = 0
                moves_in_current_round = 0
            elif betting_round == 0 and current_street == "flop":
                current_street = "turn"
                betting_round = 0
                moves_in_current_round = 0
            elif betting_round == 0 and current_street == "turn":
                current_street = "river"
                betting_round = 0
                moves_in_current_round = 0
            else:
                betting_round += 1
                moves_in_current_round = 0

        if move == "fold":
            active_players -= 1

    return dict(street_moves)


def group_moves_by_street_simple(player_moves: Dict[str, List[str]]) -> Dict[str, List[str]]:
    street_moves = {
        "preflop": [],
        "flop": [],
        "turn": [],
        "river": []
    }

    position_order = ['SB', 'BB', 'UTG', 'MP', 'CO', 'BTN']

    all_moves = []
    for position in position_order:
        if position in player_moves:
            all_moves.extend(player_moves[position])

    current_street_idx = 0
    streets = ["preflop", "flop", "turn", "river"]
    consecutive_checks = 0
    last_was_aggressive = False

    for move in all_moves:
        current_street = streets[min(current_street_idx, 3)]
        street_moves[current_street].append(move)

        if move in ["check"]:
            consecutive_checks += 1
            if consecutive_checks >= 2 and last_was_aggressive:
                current_street_idx = min(current_street_idx + 1, 3)
                consecutive_checks = 0
        elif move in ["bet", "raise"]:
            last_was_aggressive = True
            consecutive_checks = 0
        elif move == "call":
            consecutive_checks = 0

    return street_moves