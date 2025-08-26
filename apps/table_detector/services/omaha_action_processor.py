from typing import List, Union, Tuple, Dict, overload

from apps.shared.domain.moves import MoveType
from apps.shared.domain.omaha_game import OmahaGame
from apps.shared.domain.position import Position
from apps.shared.domain.street import Street


@overload
def group_moves_by_street(
        player_moves: Dict[str, List[str]]) -> Dict[Street, List[Tuple[Position, MoveType]]]:
    ...

@overload
def group_moves_by_street(
        player_moves: Dict[Position, List[MoveType]]) -> Dict[Street, List[Tuple[Position, MoveType]]]:
    ...

@overload
def group_moves_by_street(
        player_moves: Dict[Union[str, Position], List[Union[MoveType, str]]]) -> Dict[Street, List[Tuple[Position, MoveType]]]:
    ...

def group_moves_by_street(
        player_moves: Dict[Union[str, Position], List[Union[MoveType, str]]]) -> Dict[Street, List[Tuple[Position, MoveType]]]:
    """
    Groups player moves by street according to proper Omaha poker rules using state machine.

    This function serves as an adapter that converts the input format to work with
    the OmahaGame state machine, which handles all poker rule validation and
    street transition logic.

    Function supports multiple input formats via overloads:
    1. Dict[str, List[str]] - from detection pipeline (position names as strings)
    2. Dict[Position, List[MoveType]] - from test code (enums directly)  
    3. Dict[Union[str, Position], List[Union[MoveType, str]]] - mixed format

    Omaha Poker Rules:
    - A betting round ends when all active players have either called the last raise,
      folded, or (if no betting) checked
    - Blinds are posted automatically and not included in player_moves
    - Action order: EP, MP, CO, BTN, SB, BB (for voluntary actions)
    - Streets progress: preflop -> flop -> turn -> river
    - After aggression (bet/raise), all other active players must respond

    Args:
        player_moves: Dict with Position enum or position strings as keys and lists of MoveType actions
                     Actions can be MoveType or string (normalized internally)
                     Only voluntary actions, blinds excluded
                     Note: Tuple format (MoveType, amount) is no longer supported

    Returns:
        Dict with Street enum as keys and ordered lists of (Position, MoveType) tuples

    Raises:
        ValueError: If input contains invalid positions or move types
        TypeError: If input format is incorrect
    """
    # Handle empty input
    if not player_moves:
        return {Street.PREFLOP: [], Street.FLOP: [], Street.TURN: [], Street.RIVER: []}

    # Phase 1: Normalize and validate input
    normalized_moves = _normalize_player_moves(player_moves)

    # Phase 2: Build chronological action sequence
    all_actions = _build_chronological_action_sequence(normalized_moves)

    if not all_actions:
        return {Street.PREFLOP: [], Street.FLOP: [], Street.TURN: [], Street.RIVER: []}

    # Phase 3: Use OmahaGame state machine to process actions
    game = OmahaGame()

    # Add all players to the game
    for position_str in normalized_moves.keys():
        position_enum = Position.normalize_position(position_str)
        game.add_player(position_enum)

    # Start the game
    game.start_game()

    # Process all actions through the state machine
    for position_str, move in all_actions:
        position_enum = Position.normalize_position(position_str)

        # Process action if game is still active
        if not game.is_game_over():
            try:
                game.process_action(position_enum, move)
            except Exception as e:
                # If action fails, it might be because the game ended
                # In that case, we can ignore remaining actions
                if game.is_game_over():
                    break
                else:
                    # Re-raise if it's a real error
                    raise e

    # Return the final move history
    return game.get_moves_by_street()


def _normalize_player_moves(player_moves: Dict[Union[str, Position], List[Union[MoveType, str]]]) -> Dict[str, List[MoveType]]:
    """
    Normalize and validate input player moves for consistent processing.
    
    Converts mixed input formats to standardized format:
    - Position keys: Position enum or string -> normalized position string
    - Move values: MoveType, string, or (MoveType, amount) tuple -> MoveType enum
    
    Args:
        player_moves: Dict with Position enum or position strings as keys and lists of MoveType actions
                     Actions can be MoveType or string (normalized internally)
    
    Returns:
        Dict with normalized position strings as keys and lists of MoveType enums as values
        
    Raises:
        ValueError: If position string cannot be normalized or move type is invalid
        TypeError: If input types are completely invalid
    """
    if not isinstance(player_moves, dict):
        raise TypeError("player_moves must be a dictionary")
    
    normalized_moves = {}
    
    for pos_key, moves in player_moves.items():
        # Normalize position key
        if isinstance(pos_key, Position):
            normalized_pos = pos_key.value
        elif isinstance(pos_key, str):
            normalized_position_enum = Position.normalize_position(pos_key)
            normalized_pos = normalized_position_enum.value
        else:
            raise TypeError(f"Position key must be Position enum or string, got {type(pos_key)}")
        
        # Validate and normalize moves list
        if not isinstance(moves, list):
            raise TypeError(f"Moves for position {pos_key} must be a list, got {type(moves)}")
        
        normalized_move_list = []
        for i, move in enumerate(moves):
            try:
                # Convert string to MoveType if needed
                if isinstance(move, str):
                    move_type = MoveType.normalize_action(move)
                elif isinstance(move, MoveType):
                    move_type = move
                else:
                    raise TypeError(f"Move must be MoveType or string at position {pos_key}, move {i}: {type(move)}")
                
                normalized_move_list.append(move_type)
                
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid move at position {pos_key}, index {i}: {e}")
        
        normalized_moves[normalized_pos] = normalized_move_list
    
    return normalized_moves


def _build_chronological_action_sequence(normalized_moves: Dict[str, List[MoveType]]) -> List[Tuple[str, MoveType]]:
    """
    Build chronological action sequence following Omaha position order.
    
    Args:
        normalized_moves: Dict with position strings as keys and MoveType lists as values
        
    Returns:
        List of (position_string, MoveType) tuples in chronological order
    """
    position_order = [pos.value for pos in Position.get_action_order()]
    all_actions = []
    
    # Get maximum number of actions any player has
    max_actions = max(len(moves) for moves in normalized_moves.values()) if normalized_moves else 0
    
    # Reconstruct chronological action order
    for action_idx in range(max_actions):
        for position in position_order:
            if position in normalized_moves and action_idx < len(normalized_moves[position]):
                move = normalized_moves[position][action_idx]
                all_actions.append((position, move))
    
    return all_actions
