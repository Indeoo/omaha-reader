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


class OmahaGame:
    """
    Wrapper for PotLimitOmahaHoldem that maintains the same API as the original OmahaGame.
    
    This class provides a simplified interface to pokerkit's professional poker engine
    while maintaining compatibility with existing code that expects move history tracking.
    
    The wrapper handles:
    - Position mapping between Position enums and player indices
    - Action conversion between MoveType enums and pokerkit actions
    - State extraction to maintain move history format
    - Game state tracking for compatibility
    """
    
    def __init__(self, player_positions: List[Position]):
        # Move history - main output format
        self.moves_by_street: Dict[Street, List[Tuple[Position, MoveType]]] = {
            Street.PREFLOP: [],
            Street.FLOP: [],
            Street.TURN: [],
            Street.RIVER: []
        }
        
        # Position mapping
        self.position_to_index: Dict[Position, int] = {}
        self.index_to_position: Dict[int, Position] = {}

        for position in player_positions:
            self._add_player(position)

        player_count = len(player_positions)

        """Start the game - create pokerkit instance and transition to active betting"""
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
                Automation.HAND_KILLING,
                Automation.CHIPS_PUSHING,
                Automation.CHIPS_PULLING,
            ),
            True,  # Uniform antes?
            0,  # Antes
            blinds,  # Blinds (SB, BB)
            1,  # Min-bet
            starting_stacks,  # Starting stacks
            player_count,  # Number of players
        )

        # Deal hole cards to all players to make state ready for betting
        self._deal_hole_cards()

    def _add_player(self, position: Position) -> None:
        """Add a player to the game"""
        if not isinstance(position, Position):
            raise TypeError(f"Position must be Position enum, got {type(position)}")

        # Create position mapping 
        player_index = len(self.position_to_index)
        self.position_to_index[position] = player_index
        self.index_to_position[player_index] = position

    def _deal_hole_cards(self) -> None:
        """Deal hole cards to all players to make the poker state ready for betting"""
        # Deal 4 cards to each player (Omaha requires 4 hole cards)
        for player_index in range(len(self.position_to_index)):
            # Deal placeholder cards - in real usage, these would be actual cards
            # For testing purposes, we use generic Omaha hands
            if player_index == 0:
                self.poker_state.deal_hole('AsAhKsKh')  # Strong starting hand
            elif player_index == 1:
                self.poker_state.deal_hole('QdQcJsTs')  # Good starting hand
            else:
                # For additional players, cycle through some reasonable hands
                hands = [
                    'JhJd9h8s', 'ThTc9c8c', 'AcKcQhJh', '9d8d7s6c'
                ]
                hand_index = (player_index - 2) % len(hands)
                self.poker_state.deal_hole(hands[hand_index])

    def process_action(self, position: Position, action: MoveType) -> bool:
        street = self.get_current_street()

        action_result = self._execute_pokerkit_action(action)

        if not action_result:
            raise InvalidActionError(f"Invalid action: {action} on {self.get_current_street()} for {position}.", position, action, self.get_current_street())
        else:
            print(f"Action {action} for {position} successfully processed")
        # Always record the action in our move history
        self.moves_by_street[street].append((position, action))

        return True
    
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
            elif action in [MoveType.BET, MoveType.RAISE] and self.poker_state.can_complete_bet_or_raise_to():
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
