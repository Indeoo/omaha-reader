from typing import List, Dict, Optional
from enum import Enum
from dataclasses import dataclass

from loguru import logger

from src.core.domain.street import Street
from src.core.domain.detected_bid import DetectedBid
from src.core.service.template_matcher_service import Detection


class ActionType(Enum):
    FOLD = "fold"
    CALL = "call"
    RAISE = "raise"
    CHECK = "check"
    SMALL_BLIND = "sb"
    BIG_BLIND = "bb"


@dataclass
class Move:
    player_number: int  # 1-6
    action_type: ActionType
    amount: float  # Amount added this action
    street: Street
    total_pot_contribution: float  # Total contribution this street

class MoveReconstructor:

    def process_bid(self, current_game, previous_bids, current_bids):
        current_street = current_game.get_street()
        if not current_street:
            return

        moves = self.reconstruct_moves(
            current_bids=current_bids,
            previous_bids=previous_bids,
            current_street=current_street,
            positions=current_game.positions
        )

        if moves:
            current_game.add_moves(moves, current_street)
            logger.info(f"    📝 Reconstructed {len(moves)} moves for {current_street.value}:")
            for move in moves:
                action_desc = f"{move.action_type.value}"
                if move.amount > 0:
                    action_desc += f" ${move.amount:.2f}"
                player_label = f"P{move.player_number}"
                logger.info(f"        {player_label}: {action_desc}")

    def reconstruct_moves(self, current_bids: Dict[int, DetectedBid], previous_bids: Dict[int, DetectedBid],
                          current_street: Street, positions: Dict[int, Detection]) -> List[Move]:
        if not current_bids:
            return []

        moves = []

        # Get all players who might have acted
        all_players = set(list(current_bids.keys()) + list(previous_bids.keys()))

        # Find the highest bid in current state to determine betting level
        max_current_bid = max((bid.amount for bid in current_bids.values()), default=0.0)
        max_previous_bid = max((bid.amount for bid in previous_bids.values()), default=0.0)

        # Determine betting order based on positions
        betting_order = self._get_betting_order(positions)

        for player_num in betting_order:
            if player_num not in all_players:
                continue

            current_bid = current_bids.get(player_num)
            previous_bid = previous_bids.get(player_num)

            current_amount = current_bid.amount if current_bid else 0.0
            previous_amount = previous_bid.amount if previous_bid else 0.0

            # Skip if no change
            if current_amount == previous_amount:
                continue

            move = self._determine_move_type(
                player_num=player_num,
                current_bid=current_amount,
                previous_bid=previous_amount,
                max_current_bid=max_current_bid,
                max_previous_bid=max_previous_bid,
                current_street=current_street
            )

            if move:
                moves.append(move)

        return moves

    def _get_betting_order(self, positions: Dict[int, Detection]) -> List[int]:
        position_order = ['SB', 'BB', 'EP', 'MP', 'CO', 'BTN']

        position_to_player = {pos.position_name: i + 1 for i, pos in enumerate(positions.values())}

        betting_order = []
        for pos in position_order:
            if pos in position_to_player:
                betting_order.append(position_to_player[pos])

        for i in range(len(positions)):
            player_num = i + 1
            if player_num not in betting_order:
                betting_order.append(player_num)

        return betting_order

    def _determine_move_type(self, player_num: int, current_bid: float, previous_bid: float,
                             max_current_bid: float, max_previous_bid: float,
                             current_street: Street) -> Optional[Move]:
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

        if current_bid == 0.5:
            return Move(
                player_number=player_num,
                action_type=ActionType.SMALL_BLIND,
                amount=current_bid,
                street=Street.PREFLOP,
                total_pot_contribution=current_bid
            )

        if current_bid == 1:
            return Move(
                player_number=player_num,
                action_type=ActionType.BIG_BLIND,
                amount=current_bid,
                street=current_street,
                total_pot_contribution=current_bid
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