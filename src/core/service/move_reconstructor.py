from typing import List, Dict, Optional
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

        # Analyze current game state to reconstruct moves
        return self._analyze_current_game_state(current_game, current_street)

    def _analyze_current_game_state(self, current_game, street: Street) -> List[Move]:
        moves = []
        current_bids = current_game.current_bids

        if not current_bids:
            return moves

        # Find highest bid (the betting level)
        max_bid = max(current_bids.values()) if current_bids else 0.0

        for player_num in range(1, 7):
            # Check if player is still active
            if player_num not in current_game.positions:
                # Player folded (assuming they were in the game initially)
                move = Move(
                    player_number=player_num,
                    action_type=ActionType.FOLD,
                    amount=0.0,
                    street=street,
                    total_pot_contribution=0.0
                )
                moves.append(move)
                continue

            # Player is active, check their bid
            player_bid = current_bids.get(player_num, 0.0)

            if player_bid == 0:
                # Player checked/hasn't acted
                move = Move(
                    player_number=player_num,
                    action_type=ActionType.CHECK,
                    amount=0.0,
                    street=street,
                    total_pot_contribution=0.0
                )
                moves.append(move)
            elif player_bid == max_bid:
                # Player called the betting level
                move = Move(
                    player_number=player_num,
                    action_type=ActionType.CALL,
                    amount=player_bid,
                    street=street,
                    total_pot_contribution=player_bid
                )
                moves.append(move)
            elif player_bid == max_bid and max_bid > 0:
                # Player raised (has the highest bid)
                move = Move(
                    player_number=player_num,
                    action_type=ActionType.RAISE,
                    amount=player_bid,
                    street=street,
                    total_pot_contribution=player_bid
                )
                moves.append(move)

        return moves

    # def reconstruct_moves(self, current_game, previous_game: Optional) -> List[Move]:
    #     if not previous_game:
    #         return []
    #
    #     current_street = current_game.get_street()
    #     previous_street = previous_game.get_street()
    #
    #     if not current_street or not previous_street:
    #         return []
    #
    #     # If street changed, reset bids for new street
    #     if current_street != previous_street:
    #         return self._handle_street_change(current_game, previous_game)
    #
    #     # Same street - analyze bid differences
    #     return self._analyze_bid_differences(current_game, previous_game, current_street)

    def _handle_street_change(self, current_game, previous_game) -> List[Move]:
        # On street change, current bids represent new street contributions
        current_street = current_game.get_street()
        moves = []

        for player_num in range(1, 7):
            current_bid = current_game.current_bids.get(player_num, 0.0)

            # Player still in positions and has made a bid
            if player_num in current_game.positions and current_bid > 0:
                # First action on new street with money = bet/raise
                action_type = ActionType.RAISE if current_bid > 0 else ActionType.CHECK

                move = Move(
                    player_number=player_num,
                    action_type=action_type,
                    amount=current_bid,
                    street=current_street,
                    total_pot_contribution=current_bid
                )
                moves.append(move)

        return moves

    def _analyze_bid_differences(self, current_game, previous_game, street: Street) -> List[Move]:
        moves = []

        for player_num in range(1, 7):
            current_bid = current_game.current_bids.get(player_num, 0.0)
            previous_bid = previous_game.current_bids.get(player_num, 0.0)

            # Check if player folded (was in positions, now not)
            was_in_game = player_num in previous_game.positions
            still_in_game = player_num in current_game.positions

            if was_in_game and not still_in_game:
                # Player folded
                move = Move(
                    player_number=player_num,
                    action_type=ActionType.FOLD,
                    amount=0.0,
                    street=street,
                    total_pot_contribution=previous_bid
                )
                moves.append(move)
                continue

            # Player still in game, check bid changes
            if still_in_game and current_bid != previous_bid:
                bid_increase = current_bid - previous_bid
                action_type = self._determine_action_type(
                    bid_increase, current_bid, current_game.current_bids, player_num
                )

                move = Move(
                    player_number=player_num,
                    action_type=action_type,
                    amount=bid_increase,
                    street=street,
                    total_pot_contribution=current_bid
                )
                moves.append(move)

        return moves

    def _determine_action_type(self, bid_increase: float, current_bid: float,
                               all_bids: Dict[int, float], player_num: int) -> ActionType:
        if bid_increase == 0:
            return ActionType.CHECK

        # Find the highest bid from other players
        other_players_bids = [bid for pnum, bid in all_bids.items() if pnum != player_num]
        max_other_bid = max(other_players_bids) if other_players_bids else 0.0

        if current_bid == max_other_bid:
            return ActionType.CALL
        elif current_bid > max_other_bid:
            return ActionType.RAISE
        else:
            # Should not happen if bids are reliable, but default to call
            return ActionType.CALL