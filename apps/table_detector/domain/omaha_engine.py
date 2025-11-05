from typing import Dict, List, Tuple

from loguru import logger
from pokerkit import Automation, PotLimitOmahaHoldem
from shared.domain.moves import MoveType
from shared.domain.position import Position
from shared.domain.street import Street


class OmahaEngineException(Exception):
    pass


class InvalidActionError(OmahaEngineException):
    """Raised when an invalid action is attempted"""
    def __init__(self, message: str, position: Position, action: MoveType, current_street: Street):
        super().__init__(message)
        self.position = position
        self.action = action
        self.current_street = current_street


class InvalidPositionSequenceError(OmahaEngineException):
    """Raised when an invalid position sequence is attempted"""

class WrongPlayerAmount(OmahaEngineException):
    def __init__(self, message: str):
        super().__init__(message)


class OmahaEngine:
    # Street index to Street enum mapping
    STREET_INDEX_MAP = {
        0: Street.PREFLOP,
        1: Street.FLOP,
        2: Street.TURN,
        3: Street.RIVER
    }

    # Position orders for different player counts
    POSITION_ORDERS = {
        2: [Position.SMALL_BLIND, Position.BIG_BLIND],
        3: [Position.BUTTON, Position.SMALL_BLIND, Position.BIG_BLIND],
        4: [Position.CUTOFF, Position.BUTTON, Position.SMALL_BLIND, Position.BIG_BLIND],
        5: [Position.EARLY_POSITION, Position.CUTOFF, Position.BUTTON, Position.SMALL_BLIND, Position.BIG_BLIND],
        6: [Position.EARLY_POSITION, Position.MIDDLE_POSITION, Position.CUTOFF, Position.BUTTON, Position.SMALL_BLIND, Position.BIG_BLIND]
    }

    # Poker engine automations
    AUTOMATIONS = (
        Automation.ANTE_POSTING,
        Automation.BET_COLLECTION,
        Automation.BLIND_OR_STRADDLE_POSTING,
        Automation.HOLE_CARDS_SHOWING_OR_MUCKING,
        Automation.CARD_BURNING,
        Automation.BOARD_DEALING,
        Automation.HAND_KILLING,
        Automation.CHIPS_PUSHING,
        Automation.CHIPS_PULLING,
        Automation.HOLE_DEALING
    )

    def __init__(self, player_count):
        if player_count < 2:
            raise WrongPlayerAmount("Need at least 2 players to start game")

        if player_count > 6:
            raise WrongPlayerAmount("There can't be more than 6 players")

        self.moves_by_street: Dict[Street, List[Tuple[Position, MoveType]]] = {
            Street.PREFLOP: [],
            Street.FLOP: [],
            Street.TURN: [],
            Street.RIVER: []
        }

        starting_stacks = [100] * player_count  # Default stack size
        blinds = (0.5, 1)  # Default blinds (SB, BB)

        self.poker_state = PotLimitOmahaHoldem.create_state(
            self.AUTOMATIONS,
            True,  # Uniform antes?
            0,  # Antes
            blinds,  # Blinds (SB, BB)
            1,  # Min-bet
            starting_stacks,  # Starting stacks
            player_count,  # Number of players
        )

        self.seat_mapping = self._get_seat_to_position_mapping()

    def process_action(self, position: Position, action: MoveType):

        if position != self.get_current_position():
            raise InvalidPositionSequenceError("Wrong position sequence in OmahaEngine")

        street = self.get_current_street()
        action_result = self._execute_pokerkit_action(action)

        if not action_result:
            raise InvalidActionError(f"Invalid action: {action} on {street} for {position}.", position, action, street)

        logger.info(f"Action {action} for {position} successfully processed")

        self.moves_by_street[street].append((position, action))

    def simulate_all_moves(self, player_moves: dict[Position, list[MoveType]]):
        while any(player_moves.values()):
            current_position = self.get_current_position()
            moves = player_moves[current_position]

            if not moves:
                # Gather diagnostic information
                positions_with_moves = {pos: mvs for pos, mvs in player_moves.items() if mvs}
                street = self.get_current_street()

                error_msg = (
                    f"Position sequence error: {current_position} expected to act but has no moves. "
                    f"Street: {street}. "
                    f"Positions with pending moves: {list(positions_with_moves.keys())}. "
                    f"Pending moves: {positions_with_moves}"
                )
                raise InvalidPositionSequenceError(error_msg)

            self.process_action(current_position, moves.pop(0))

    def _execute_pokerkit_action(self, action: MoveType) -> bool:
        try:
            if action == MoveType.FOLD and self.poker_state.can_fold():
                self.poker_state.fold()
                return True
            elif action == MoveType.CHECK and self.poker_state.can_check_or_call():
                calling_amount = self.poker_state.checking_or_calling_amount
                if calling_amount is None or calling_amount == 0:
                    self.poker_state.check_or_call()
                    return True
            elif action == MoveType.CALL and self.poker_state.can_check_or_call():
                calling_amount = self.poker_state.checking_or_calling_amount
                if calling_amount is not None and calling_amount > 0:
                    self.poker_state.check_or_call()
                    return True
            elif action in [MoveType.BET, MoveType.CALL, MoveType.RAISE] and self.poker_state.can_complete_bet_or_raise_to():
                min_amount = self.poker_state.min_completion_betting_or_raising_to_amount
                if min_amount is not None:
                    self.poker_state.complete_bet_or_raise_to(min_amount)
                    return True
        except Exception:
            return False

        return False

    def get_current_street(self) -> Street:
        street_index = self.poker_state.street_index
        street = self.STREET_INDEX_MAP.get(street_index)

        if street is None:
            raise ValueError(f"Invalid street index: {street_index}")

        return street

    def get_moves_by_street(self) -> Dict[Street, List[Tuple[Position, MoveType]]]:
        return self.moves_by_street.copy()

    def get_current_position(self):
        return self.seat_mapping[self.poker_state.actor_index]

    def _get_seat_to_position_mapping(self) -> Dict[int, Position]:
        player_count = self.poker_state.player_count
        opener_index = self.poker_state.opener_index
        position_order = self._get_position_order_for_player_count(player_count)

        return {
            i: position_order[(i - opener_index) % player_count]
            for i in range(player_count)
        }
    
    def _get_position_order_for_player_count(self, player_count: int) -> List[Position]:
        if player_count not in self.POSITION_ORDERS:
            raise ValueError(f"Unsupported player count: {player_count}. Supported range: 2-6 players")

        return self.POSITION_ORDERS[player_count]

    @staticmethod
    def convert_to_position_actions(actions, positions: Dict[int, Position]) -> Dict[Position, List[MoveType]]:
        result = {}

        # First, add all positions to the result (even without actions)
        for player_id, position_enum in positions.items():
            # Initialize with empty action list
            result[position_enum] = []

        # Then, process actual actions for players that have them
        for player_id, detection_list in actions.items():
            if player_id in positions:
                position_enum = positions[player_id]

                # Convert detection names to MoveType enums
                move_types = []
                for d in detection_list:
                    try:
                        move_type = MoveType.normalize_action(d.name)
                        move_types.append(move_type)
                    except ValueError as e:
                        logger.warning(f"Skipping invalid move '{d.name}' for position {position_enum}: {e}")
                        continue

                # Add moves to the existing position (which may already be initialized with empty list)
                result[position_enum].extend(move_types)

        logger.info(result)

        return result

