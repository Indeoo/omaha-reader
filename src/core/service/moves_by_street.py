from typing import List, Union, Tuple, Dict
from src.core.domain.moves import MoveType
from src.core.domain.position import Position
from src.core.domain.street import Street
from src.core.service.omaha_game import OmahaGame


def _normalize_player_moves(player_moves: Dict[Union[str, Position], List[Union[MoveType, str, Tuple[Union[MoveType, str], float]]]]) -> Dict[str, List[MoveType]]:
    """
    Normalize and validate input player moves for consistent processing.
    
    Converts mixed input formats to standardized format:
    - Position keys: Position enum or string -> normalized position string
    - Move values: MoveType, string, or (MoveType, amount) tuple -> MoveType enum
    
    Args:
        player_moves: Dict with Position enum or position strings as keys and lists of MoveType actions
                     Actions can be MoveType, string, or tuples (MoveType, amount)
    
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
            try:
                normalized_position_enum = Position.normalize_position(pos_key)
                normalized_pos = normalized_position_enum.value
            except ValueError:
                # Keep original string for backward compatibility
                normalized_pos = pos_key
        else:
            raise TypeError(f"Position key must be Position enum or string, got {type(pos_key)}")
        
        # Validate and normalize moves list
        if not isinstance(moves, list):
            raise TypeError(f"Moves for position {pos_key} must be a list, got {type(moves)}")
        
        normalized_move_list = []
        for i, move in enumerate(moves):
            try:
                # Extract MoveType from various input formats
                if isinstance(move, tuple):
                    # Handle (MoveType, amount) tuples
                    if len(move) < 1:
                        raise ValueError(f"Empty tuple at position {pos_key}, move {i}")
                    raw_move = move[0]
                elif isinstance(move, (MoveType, str)):
                    raw_move = move
                else:
                    raise TypeError(f"Invalid move type at position {pos_key}, move {i}: {type(move)}")
                
                # Convert string to MoveType if needed
                if isinstance(raw_move, str):
                    move_type = MoveType.normalize_action(raw_move)
                elif isinstance(raw_move, MoveType):
                    move_type = raw_move
                else:
                    raise TypeError(f"Move must be MoveType or string at position {pos_key}, move {i}: {type(raw_move)}")
                
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


def _process_betting_round(all_actions: List[Tuple[str, MoveType]], action_idx: int, current_street: Street, 
                          active_players: List[str], folded_players: set) -> Tuple[List[Tuple[Position, MoveType]], int, bool]:
    """
    Process a single betting round according to Omaha poker rules.
    
    In Omaha, a betting round is complete when:
    1. All active players have either called the last bet/raise, folded, or checked (if no betting)
    2. After any bet/raise, all players who acted before must respond
    
    Args:
        all_actions: Complete list of chronological actions
        action_idx: Current index in all_actions
        current_street: Current street being processed
        active_players: List of active player position strings
        folded_players: Set of folded player position strings
        
    Returns:
        Tuple of (street_actions, new_action_idx, game_over_flag)
        - street_actions: List of (Position, MoveType) tuples for this street
        - new_action_idx: Updated action index
        - game_over_flag: True if game should end (≤1 active player)
    """
    street_actions = []
    players_acted_this_round = set()
    last_aggression_point = None  # Track when last aggression occurred
    
    # Continue until all players have acted appropriately for this betting round
    while action_idx < len(all_actions):
        position_str, move = all_actions[action_idx]
        
        # Skip actions from already folded players
        if position_str in folded_players:
            action_idx += 1
            continue
        
        # Record the action with position enum
        position_enum = Position.normalize_position(position_str)
        street_actions.append((position_enum, move))
        action_idx += 1
        
        # Track that this player has acted this round
        players_acted_this_round.add(position_str)
        
        # Update game state based on action type
        if move == MoveType.FOLD:
            folded_players.add(position_str)
            active_players.remove(position_str)
            
            # Check if only one player remains - game over
            if len(active_players) <= 1:
                # Process any remaining actions and end
                while action_idx < len(all_actions):
                    remaining_pos, remaining_move = all_actions[action_idx]
                    if remaining_pos not in folded_players:
                        remaining_position_enum = Position.normalize_position(remaining_pos)
                        street_actions.append((remaining_position_enum, remaining_move))
                    action_idx += 1
                return street_actions, action_idx, True
                
        elif move in [MoveType.BET, MoveType.RAISE]:
            # Aggression occurred - mark this point and reset who needs to act
            last_aggression_point = len(street_actions) - 1
            players_acted_this_round = {position_str}  # Reset - only aggressor has acted to current bet level
            
        elif move in [MoveType.CALL, MoveType.CHECK]:
            # Passive action - player has responded appropriately
            pass
        
        # Check if betting round is complete
        active_players_set = set(active_players)
        if players_acted_this_round == active_players_set:
            # All active players have acted to the current bet level
            if last_aggression_point is None:
                # No aggression this round - all checks, round complete
                break
            else:
                # There was aggression and all active players have responded - round complete
                break
    
    return street_actions, action_idx, False


def group_moves_by_street(player_moves: Dict[Union[str, Position], List[Union[MoveType, str, Tuple[Union[MoveType, str], float]]]]) -> Dict[Street, List[Tuple[Position, MoveType]]]:
    """
    Groups player moves by street according to proper Omaha poker rules using state machine.
    
    This function serves as an adapter that converts the input format to work with
    the OmahaGame state machine, which handles all poker rule validation and
    street transition logic.
    
    Omaha Poker Rules:
    - A betting round ends when all active players have either called the last raise, 
      folded, or (if no betting) checked
    - Blinds are posted automatically and not included in player_moves
    - Action order: EP, MP, CO, BTN, SB, BB (for voluntary actions)
    - Streets progress: preflop -> flop -> turn -> river
    - After aggression (bet/raise), all other active players must respond
    
    Args:
        player_moves: Dict with Position enum or position strings as keys and lists of MoveType actions
                     Actions can be MoveType, string, or tuples (MoveType, amount)
                     Only voluntary actions, blinds excluded
    
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


def group_moves_by_street_simple(player_moves: Dict[Union[str, Position], List[Union[MoveType, str]]]) -> Dict[Street, List[Tuple[Position, MoveType]]]:
    """
    Simple approach to group moves by street.
    Uses consistent position order and basic street transition logic.
    
    Note: This is a simplified version that doesn't implement full Omaha poker rules.
    For proper rule compliance, use group_moves_by_street() instead.
    """
    street_moves = {
        Street.PREFLOP: [],
        Street.FLOP: [],
        Street.TURN: [],
        Street.RIVER: []
    }

    # Use same position order as main function for consistency
    position_order = [pos.value for pos in Position.get_action_order()]
    
    # Normalize position keys to strings for internal processing
    normalized_player_moves = {}
    for pos_key, moves in player_moves.items():
        if isinstance(pos_key, Position):
            normalized_player_moves[pos_key.value] = moves
        else:
            # Validate and normalize string positions
            try:
                normalized_pos = Position.normalize_position(pos_key)
                normalized_player_moves[normalized_pos.value] = moves
            except ValueError:
                # Keep original string if it can't be normalized (for backward compatibility)
                normalized_player_moves[pos_key] = moves

    all_moves = []
    for position in position_order:
        if position in normalized_player_moves:
            for move in normalized_player_moves[position]:
                # Convert string to MoveType if needed
                if isinstance(move, str):
                    move_type = MoveType.normalize_action(move)
                else:
                    move_type = move
                position_enum = Position.normalize_position(position)
                all_moves.append((position_enum, move_type))

    current_street_idx = 0
    streets = [Street.PREFLOP, Street.FLOP, Street.TURN, Street.RIVER]
    consecutive_checks = 0
    last_was_aggressive = False

    for position_move_pair in all_moves:
        current_street = streets[min(current_street_idx, 3)]
        street_moves[current_street].append(position_move_pair)
        position_enum, move = position_move_pair

        if move == MoveType.CHECK:
            consecutive_checks += 1
            if consecutive_checks >= 2 and not last_was_aggressive:
                current_street_idx = min(current_street_idx + 1, 3)
                consecutive_checks = 0
                last_was_aggressive = False
        elif move in [MoveType.BET, MoveType.RAISE]:
            last_was_aggressive = True
            consecutive_checks = 0
        elif move == MoveType.CALL:
            consecutive_checks = 0
            # After calls, if last_was_aggressive, round might end
            if last_was_aggressive:
                current_street_idx = min(current_street_idx + 1, 3)
                last_was_aggressive = False
        elif move == MoveType.FOLD:
            consecutive_checks = 0

    return street_moves