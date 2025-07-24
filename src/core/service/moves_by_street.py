from collections import defaultdict
from typing import List, Union, Tuple, Dict


def group_moves_by_street(player_moves: Dict[int, List[Union[str, Tuple[str, float]]]]) -> Dict[str, List[str]]:
    street_moves = defaultdict(list)

    # Collect all moves with player info to maintain order
    all_moves_ordered = []

    # First, we need to reconstruct the action sequence
    # In poker, action typically goes in position order
    # For simplicity, we'll assume players act in numerical order per round

    # Find max rounds (assuming each player acts once per round)
    max_rounds = max(len(moves) for moves in player_moves.values()) if player_moves else 0

    # Reconstruct action order round by round
    for round_idx in range(max_rounds):
        for player_num in sorted(player_moves.keys()):
            if round_idx < len(player_moves[player_num]):
                move = player_moves[player_num][round_idx]
                # Extract just the action if it's a tuple
                if isinstance(move, tuple):
                    move = move[0]
                all_moves_ordered.append(move)

    # Now assign moves to streets based on betting rounds
    # In Omaha: preflop, flop, turn, river
    # Each street can have multiple betting rounds

    current_street = "preflop"
    betting_round = 0
    moves_in_current_round = 0
    active_players = len([p for p, moves in player_moves.items() if moves and moves[0] != "fold"])

    for i, move in enumerate(all_moves_ordered):
        street_moves[current_street].append(move)
        moves_in_current_round += 1

        # Check if betting round is complete
        # A round ends when all active players have acted
        if moves_in_current_round >= active_players:
            # Check if we should move to next street
            # This happens after first betting round of each street
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
                # Same street, next betting round
                betting_round += 1
                moves_in_current_round = 0

        # Update active players if someone folded
        if move == "fold":
            active_players -= 1

    return dict(street_moves)


# Alternative: Simple approach based on action patterns
def group_moves_by_street_simple(player_moves: Dict[int, List[str]]) -> Dict[str, List[str]]:
    street_moves = {
        "preflop": [],
        "flop": [],
        "turn": [],
        "river": []
    }

    # Flatten all moves
    all_moves = []
    for player_num in sorted(player_moves.keys()):
        all_moves.extend(player_moves[player_num])

    # Simple heuristic: look for patterns
    # Betting typically slows down on later streets
    # First aggressive action sequence = preflop
    # Then flop, turn, river

    current_street_idx = 0
    streets = ["preflop", "flop", "turn", "river"]
    consecutive_checks = 0
    last_was_aggressive = False

    for move in all_moves:
        current_street = streets[min(current_street_idx, 3)]
        street_moves[current_street].append(move)

        # Detect street changes based on action patterns
        if move in ["check"]:
            consecutive_checks += 1
            # Multiple checks might indicate new street
            if consecutive_checks >= 2 and last_was_aggressive:
                current_street_idx = min(current_street_idx + 1, 3)
                consecutive_checks = 0
        elif move in ["bet", "raise"]:
            last_was_aggressive = True
            consecutive_checks = 0
        elif move == "call":
            consecutive_checks = 0

    return street_moves