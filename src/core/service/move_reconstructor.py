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

#
# class MoveReconstructor:
#
#     def reconstruct_moves(self, current_game) -> List[Move]:
#         current_street = current_game.get_street()
#         if not current_street:
#             return []
#
#         moves = []
#         current_bids = current_game.current_bids
#
#         if not current_bids:
#             return moves
#
#         # Find highest bid (the betting level)
#         max_bid = max(current_bids.values()) if current_bids else 0.0
#
#         for player_num in range(1, 7):
#             player_bid = current_bids.get(player_num, 0.0)
#
#             if player_bid == 0:
#                 # No bid detected = player folded
#                 move = Move(
#                     player_number=player_num,
#                     action_type=ActionType.FOLD,
#                     amount=0.0,
#                     street=current_street,
#                     total_pot_contribution=0.0
#                 )
#                 moves.append(move)
#             elif player_bid == max_bid and player_bid > 0:
#                 # Has the highest bid = raised (or initial bet)
#                 move = Move(
#                     player_number=player_num,
#                     action_type=ActionType.RAISE,
#                     amount=player_bid,
#                     street=current_street,
#                     total_pot_contribution=player_bid
#                 )
#                 moves.append(move)
#             else:
#                 # Has a bid but not the highest = called
#                 move = Move(
#                     player_number=player_num,
#                     action_type=ActionType.CALL,
#                     amount=player_bid,
#                     street=current_street,
#                     total_pot_contribution=player_bid
#                 )
#                 moves.append(move)
#
#         return moves


class MoveReconstructor:

    def reconstruct_moves(self, current_bids: Dict[int, float], previous_bids: Dict[int, float],
                          current_street: Street, positions: Dict[int, str]) -> List[Move]:
        """
        Reconstruct moves between two game states by comparing bid changes

        Args:
            current_bids: Current bid amounts for each player
            previous_bids: Previous bid amounts for each player
            current_street: Current street being played
            positions: Player positions (for betting order)

        Returns:
            List of moves that occurred between states
        """
        if not current_bids:
            return []

        moves = []

        # Get all players who might have acted
        all_players = set(list(current_bids.keys()) + list(previous_bids.keys()))

        # Find the highest bid in current state to determine betting level
        max_current_bid = max(current_bids.values()) if current_bids else 0.0
        max_previous_bid = max(previous_bids.values()) if previous_bids else 0.0

        # Determine betting order based on positions
        betting_order = self._get_betting_order(positions)

        for player_num in betting_order:
            if player_num not in all_players:
                continue

            current_bid = current_bids.get(player_num, 0.0)
            previous_bid = previous_bids.get(player_num, 0.0)

            # Skip if no change
            if current_bid == previous_bid:
                continue

            move = self._determine_move_type(
                player_num=player_num,
                current_bid=current_bid,
                previous_bid=previous_bid,
                max_current_bid=max_current_bid,
                max_previous_bid=max_previous_bid,
                current_street=current_street
            )

            if move:
                moves.append(move)

        return moves

    def _get_betting_order(self, positions: Dict[int, str]) -> List[int]:
        """
        Determine betting order based on positions
        Standard order: SB -> BB -> UTG -> MP -> CO -> BTN
        """
        position_order = ['SB', 'BB', 'UTG', 'MP', 'CO', 'BTN']

        # Create mapping of position to player
        position_to_player = {pos: player for player, pos in positions.items()}

        # Build betting order
        betting_order = []
        for pos in position_order:
            if pos in position_to_player:
                betting_order.append(position_to_player[pos])

        # Add any players not in standard positions
        for player_num in positions.keys():
            if player_num not in betting_order:
                betting_order.append(player_num)

        return betting_order

    def _determine_move_type(self, player_num: int, current_bid: float, previous_bid: float,
                             max_current_bid: float, max_previous_bid: float,
                             current_street: Street) -> Optional[Move]:
        """
        Determine what type of move a player made based on bid changes
        """
        bid_change = current_bid - previous_bid

        # Player folded (had money before, now has 0)
        if previous_bid > 0 and current_bid == 0:
            return Move(
                player_number=player_num,
                action_type=ActionType.FOLD,
                amount=0.0,
                street=current_street,
                total_pot_contribution=0.0
            )

        # Player didn't act or folded from start
        if current_bid == 0:
            return Move(
                player_number=player_num,
                action_type=ActionType.FOLD,
                amount=0.0,
                street=current_street,
                total_pot_contribution=0.0
            )

        # Player increased their bid
        if bid_change > 0:
            # Check if this is a raise (creating new betting level) or call (matching existing)
            if current_bid > max_previous_bid:
                # This is a raise - player created new betting level
                return Move(
                    player_number=player_num,
                    action_type=ActionType.RAISE,
                    amount=bid_change,
                    street=current_street,
                    total_pot_contribution=current_bid
                )
            else:
                # This is a call - player matched existing betting level
                return Move(
                    player_number=player_num,
                    action_type=ActionType.CALL,
                    amount=bid_change,
                    street=current_street,
                    total_pot_contribution=current_bid
                )

        # No bid change but player has money (check)
        if bid_change == 0 and current_bid == max_current_bid and max_current_bid == 0:
            return Move(
                player_number=player_num,
                action_type=ActionType.CHECK,
                amount=0.0,
                street=current_street,
                total_pot_contribution=current_bid
            )

        return None