from typing import List
from enum import Enum
from dataclasses import dataclass

from src.core.domain.street import Street


class ActionType(Enum):
    FOLD = "fold"
    CALL = "call"
    RAISE = "raise"
    CHECK = "check"


@dataclass
class Move:
    player_number: int  # 1-6
    action_type: ActionType
    amount: float  # Amount added this action
    street: Street
    total_pot_contribution: float  # Total contribution this street


class MoveReconstructor:

    def reconstruct_moves(self, current_game) -> List[Move]:
        current_street = current_game.get_street()
        if not current_street:
            return []

        moves = []
        current_bids = current_game.current_bids

        if not current_bids:
            return moves

        # Find highest bid (the betting level)
        max_bid = max(current_bids.values()) if current_bids else 0.0

        for player_num in range(1, 7):
            player_bid = current_bids.get(player_num, 0.0)

            if player_bid == 0:
                # No bid detected = player folded
                move = Move(
                    player_number=player_num,
                    action_type=ActionType.FOLD,
                    amount=0.0,
                    street=current_street,
                    total_pot_contribution=0.0
                )
                moves.append(move)
            elif player_bid == max_bid and player_bid > 0:
                # Has the highest bid = raised (or initial bet)
                move = Move(
                    player_number=player_num,
                    action_type=ActionType.RAISE,
                    amount=player_bid,
                    street=current_street,
                    total_pot_contribution=player_bid
                )
                moves.append(move)
            else:
                # Has a bid but not the highest = called
                move = Move(
                    player_number=player_num,
                    action_type=ActionType.CALL,
                    amount=player_bid,
                    street=current_street,
                    total_pot_contribution=player_bid
                )
                moves.append(move)

        return moves