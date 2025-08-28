from typing import List, Tuple, Dict

from shared.domain.moves import MoveType
from table_detector.domain.omaha_game import OmahaGame
from shared.domain.position import Position
from shared.domain.street import Street


def group_moves_by_street(player_moves: Dict[Position, List[MoveType]]) -> Dict[Street, List[Tuple[Position, MoveType]]]:
    """
    Groups player moves by street according to proper Omaha poker rules using state machine.

    This function serves as an adapter that converts the input format to work with
    the OmahaGame state machine, which handles all poker rule validation and
    street transition logic.

    Function supports input format:
    - Dict[Position, List[MoveType]] - Position enums with MoveType enums
    
    Note: The detection pipeline now converts strings to enums before calling this function,
    providing stronger type safety throughout the system.

    Omaha Poker Rules:
    - A betting round ends when all active players have either called the last raise,
      folded, or (if no betting) checked
    - Blinds are posted automatically and not included in player_moves
    - Action order: EP, MP, CO, BTN, SB, BB (for voluntary actions)
    - Streets progress: preflop -> flop -> turn -> river
    - After aggression (bet/raise), all other active players must respond

    Args:
        player_moves: Dict with Position enum keys and lists of MoveType enum values
                     Only voluntary actions, blinds excluded
                     All normalization is now done upstream in convert_to_position_actions()

    Returns:
        Dict with Street enum as keys and ordered lists of (Position, MoveType) tuples

    Raises:
        ValueError: If input contains invalid positions or move types
        TypeError: If input format is incorrect
    """
    # Handle empty input
    if not player_moves:
        return {Street.PREFLOP: [], Street.FLOP: [], Street.TURN: [], Street.RIVER: []}

    # Phase 1: Validate input
    _validate_input(player_moves)

    # Phase 2: Build chronological action sequence
    all_actions = _build_chronological_action_sequence(player_moves)

    if not all_actions:
        return {Street.PREFLOP: [], Street.FLOP: [], Street.TURN: [], Street.RIVER: []}

    # Phase 3: Use OmahaGame state machine to process actions
    game = execute_game(all_actions, player_moves)

    return game.get_moves_by_street()


def execute_game(all_actions, player_moves):
    game = OmahaGame()
    # Add all players to the game
    for position in player_moves.keys():
        game.add_player(position)
    # Start the game
    game.start_game()
    # Process all actions through the state machine
    for position, move in all_actions:
        # Process action if game is still active
        if not game.is_game_over():
            try:
                game.process_action(position, move)
            except Exception as e:
                # If action fails, it might be because the game ended
                # In that case, we can ignore remaining actions
                if game.is_game_over():
                    break
                else:
                    # Re-raise if it's a real error
                    raise e
    # Return the final move history
    return game


def _validate_input(player_moves: Dict[Position, List[MoveType]]) -> None:
    """
    Validate input types and structure for player moves.
    
    Args:
        player_moves: Dict with Position enum keys and MoveType enum values
        
    Raises:
        TypeError: If input types are incorrect
    """
    if not isinstance(player_moves, dict):
        raise TypeError("player_moves must be a dictionary")
    
    for pos_key, moves in player_moves.items():
        # Validate Position enum key
        if not isinstance(pos_key, Position):
            raise TypeError(f"Position key must be Position enum, got {type(pos_key)}")
        
        # Validate moves list
        if not isinstance(moves, list):
            raise TypeError(f"Moves for position {pos_key} must be a list, got {type(moves)}")
        
        # Validate all moves are MoveType enums
        for i, move in enumerate(moves):
            if not isinstance(move, MoveType):
                raise TypeError(f"Move must be MoveType enum at position {pos_key}, move {i}: got {type(move)}")


def _build_chronological_action_sequence(player_moves: Dict[Position, List[MoveType]]) -> List[Tuple[Position, MoveType]]:
    """
    Build chronological action sequence following Omaha position order.
    
    Args:
        player_moves: Dict with Position enum keys and MoveType lists as values
        
    Returns:
        List of (Position, MoveType) tuples in chronological order
    """
    position_order = Position.get_action_order()
    all_actions = []
    
    # Get maximum number of actions any player has
    max_actions = max(len(moves) for moves in player_moves.values()) if player_moves else 0
    
    # Reconstruct chronological action order
    for action_idx in range(max_actions):
        for position in position_order:
            if position in player_moves and action_idx < len(player_moves[position]):
                move = player_moves[position][action_idx]
                all_actions.append((position, move))
    
    return all_actions
