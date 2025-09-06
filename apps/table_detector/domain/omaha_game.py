from typing import Dict, List, Tuple

from pokerkit import Automation, PotLimitOmahaHoldem
from shared.domain.moves import MoveType
from shared.domain.position import Position
from shared.domain.street import Street


class InvalidActionError(Exception):
    """Raised when an invalid action is attempted"""
    def __init__(self, message: str, position: Position, action: MoveType, current_street: Street):
        super().__init__(message)
        self.position = position
        self.action = action
        self.current_street = current_street


class InvalidPositionSequenceError(Exception):
    """Raised when an invalid position sequence is attempted"""


class OmahaGame:
    def __init__(self, player_positions: List[Position]):
        self.moves_by_street: Dict[Street, List[Tuple[Position, MoveType]]] = {
            Street.PREFLOP: [],
            Street.FLOP: [],
            Street.TURN: [],
            Street.RIVER: []
        }

        # Track active players for position sequence validation
        self.active_players: set[Position] = set(player_positions)

        player_count = len(player_positions)

        if player_count < 2:
            raise ValueError("Need at least 2 players to start game")

        starting_stacks = [100] * player_count  # Default stack size
        blinds = (0.5, 1)  # Default blinds (SB, BB)

        self.poker_state = PotLimitOmahaHoldem.create_state(
            (
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
            ),
            True,  # Uniform antes?
            0,  # Antes
            blinds,  # Blinds (SB, BB)
            1,  # Min-bet
            starting_stacks,  # Starting stacks
            player_count,  # Number of players
        )


    def _validate_position_sequence(self, position: Position) -> bool:
        if position not in self.active_players:
            return False
            
        current_street = self.get_current_street()
        current_moves = self.moves_by_street[current_street]
        
        # Get proper action order for current street
        if current_street == Street.PREFLOP:
            action_order = Position.get_action_order()
        else:
            action_order = Position.get_postflop_action_order()
        
        # Filter action order to only include active players in this game
        game_action_order = [pos for pos in action_order if pos in self.active_players]
        
        if not game_action_order:
            return False
            
        # If this is the first action on this street, first player should act
        if not current_moves:
            expected_first_player = game_action_order[0]
            return position == expected_first_player
            
        # Find who acted last and determine next expected player
        last_action_position = current_moves[-1][0]
        
        # Find the next active player after the last action in full action order
        last_player_index_in_full_order = action_order.index(last_action_position)
        
        # Look for next active player starting from the position after last action
        for i in range(1, len(action_order)):
            next_index = (last_player_index_in_full_order + i) % len(action_order)
            next_position = action_order[next_index]
            if next_position in self.active_players:
                return position == next_position
                
        # No active players found (shouldn't happen)
        return False

    def process_action(self, position: Position, action: MoveType):
        street = self.get_current_street()

        # Validate position sequence (optional - can be disabled for testing)
        if not self._validate_position_sequence(position):
            raise InvalidPositionSequenceError(f"Invalid position sequence: {position} cannot act on {street}", position, action, street)

        action_result = self._execute_pokerkit_action(action)

        if not action_result:
            raise InvalidActionError(f"Invalid action: {action} on {street} for {position}.", position, action, street)
        else:
            print(f"Action {action} for {position} successfully processed")
        
        # Update active players if fold action
        if action == MoveType.FOLD:
            self.active_players.discard(position)
            
        # Always record the action in our move history
        self.moves_by_street[street].append((position, action))

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
                # Use minimum bet/raise amount
                min_amount = self.poker_state.min_completion_betting_or_raising_to_amount
                if min_amount is not None:
                    self.poker_state.complete_bet_or_raise_to(min_amount)
                    return True
        except Exception:
            return False

        return False

    def get_current_street(self) -> Street:
        street_index = self.poker_state.street_index

        if street_index == 0:
            return Street.PREFLOP
        elif street_index == 1:
            return Street.FLOP
        elif street_index == 2:
            return Street.TURN
        elif street_index == 3:
            return Street.RIVER
        else:
            raise Exception(f"Invalid street index: {street_index}")

    def get_moves_by_street(self) -> Dict[Street, List[Tuple[Position, MoveType]]]:
        """Get the complete move history organized by street"""
        return self.moves_by_street.copy()

    def get_current_position(self):
        return self.get_seat_to_position_mapping()[self.poker_state.actor_index]

    def get_seat_to_position_mapping(self) -> Dict[int, Position]:
        """
        Get mapping from PokerKit seat indices to Position enums based on 
        player count and opener index.
        
        Returns:
            Dict[int, Position]: Mapping from seat index (0 to player_count-1) to Position
        """
        player_count = self.poker_state.player_count
        opener_index = self.poker_state.opener_index
        
        # Get the position order based on player count
        position_order = self._get_position_order_for_player_count(player_count)
        
        # Create mapping by rotating positions based on opener_index
        seat_to_position = {}
        for i in range(player_count):
            # PokerKit seat index
            seat_index = i
            # Corresponding position index (rotated by opener_index)
            position_index = (i - opener_index) % player_count
            # Map seat to position
            seat_to_position[seat_index] = position_order[position_index]
        
        return seat_to_position
    
    def _get_position_order_for_player_count(self, player_count: int) -> List[Position]:
        """
        Get the position order for a given player count in poker action order.
        
        Args:
            player_count: Number of players (2-6)
            
        Returns:
            List[Position]: Positions in poker action order for the given player count
        """
        if player_count == 2:
            # Heads-up: SB acts first preflop, BB acts first postflop
            return [Position.SMALL_BLIND, Position.BIG_BLIND]
        elif player_count == 3:
            # 3-handed: BTN, SB, BB
            return [Position.BUTTON, Position.SMALL_BLIND, Position.BIG_BLIND]
        elif player_count == 4:
            # 4-handed: CO, BTN, SB, BB
            return [Position.CUTOFF, Position.BUTTON, Position.SMALL_BLIND, Position.BIG_BLIND]
        elif player_count == 5:
            # 5-handed: EP, CO, BTN, SB, BB
            return [Position.EARLY_POSITION, Position.CUTOFF, Position.BUTTON, Position.SMALL_BLIND, Position.BIG_BLIND]
        elif player_count == 6:
            # 6-max: EP, MP, CO, BTN, SB, BB
            return [Position.EARLY_POSITION, Position.MIDDLE_POSITION, Position.CUTOFF, Position.BUTTON, Position.SMALL_BLIND, Position.BIG_BLIND]
        else:
            raise ValueError(f"Unsupported player count: {player_count}. Supported range: 2-6 players")
