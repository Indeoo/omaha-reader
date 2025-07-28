from typing import List, Union, Tuple, Dict
from src.core.domain.moves import MoveType
from src.core.domain.position import Position
from src.core.domain.street import Street


def group_moves_by_street(player_moves: Dict[Union[str, Position], List[Union[MoveType, str, Tuple[Union[MoveType, str], float]]]]) -> Dict[Street, List[MoveType]]:
    """
    Groups player moves by street according to proper Omaha poker rules.
    
    Omaha Poker Rules:
    - A betting round ends when all active players have either called the last raise, 
      folded, or (if no betting) checked
    - Blinds are posted automatically and not included in player_moves
    - Action order: EP, MP, CO, BTN, SB, BB (for voluntary actions)
    - Streets progress: preflop -> flop -> turn -> river
    - After aggression (bet/raise), all other active players must respond
    
    Args:
        player_moves: Dict with Position enum or position strings as keys and lists of MoveType actions
                     Actions can be MoveType or tuples (MoveType, amount)
                     Only voluntary actions, blinds excluded
    
    Returns:
        Dict with Street enum as keys and ordered lists of MoveType actions
    """
    if not player_moves:
        return {Street.PREFLOP: [], Street.FLOP: [], Street.TURN: [], Street.RIVER: []}
    
    street_moves = {
        Street.PREFLOP: [],
        Street.FLOP: [],
        Street.TURN: [],
        Street.RIVER: []
    }

    # Action order for Omaha: EP acts first for voluntary actions
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

    # Build chronological action sequence
    all_actions = []
    max_actions = max(len(moves) for moves in normalized_player_moves.values()) if normalized_player_moves else 0
    
    # Reconstruct chronological action order
    for action_idx in range(max_actions):
        for position in position_order:
            if position in normalized_player_moves and action_idx < len(normalized_player_moves[position]):
                action = normalized_player_moves[position][action_idx]
                # Extract and normalize MoveType from tuple if needed
                if isinstance(action, tuple):
                    raw_move = action[0]
                else:
                    raw_move = action
                
                # Convert string to MoveType if needed
                if isinstance(raw_move, str):
                    move_type = MoveType.normalize_action(raw_move)
                else:
                    move_type = raw_move
                    
                all_actions.append((position, move_type))
    
    if not all_actions:
        return street_moves
    
    # State tracking for proper Omaha poker rules
    streets = [Street.PREFLOP, Street.FLOP, Street.TURN, Street.RIVER]
    current_street_idx = 0
    action_idx = 0
    folded_players = set()
    
    # Process all actions according to Omaha betting round rules
    while action_idx < len(all_actions) and current_street_idx < 4:
        current_street = streets[current_street_idx]
        
        # Get active players for this street
        active_players = [pos for pos in position_order 
                         if pos in normalized_player_moves and pos not in folded_players]
        
        if len(active_players) <= 1:
            # Game over - process remaining actions if any
            while action_idx < len(all_actions):
                _, move = all_actions[action_idx]
                street_moves[current_street].append(move)
                action_idx += 1
            break
        
        # Process betting round
        betting_round_complete = False
        last_aggressor_position = None
        players_yet_to_act = set(active_players)
        
        while action_idx < len(all_actions) and not betting_round_complete:
            position, move = all_actions[action_idx]
            
            # Skip actions from already folded players
            if position in folded_players:
                action_idx += 1
                continue
            
            # Record the action
            street_moves[current_street].append(move)
            action_idx += 1
            
            # Update game state based on action type
            if move == MoveType.FOLD:
                folded_players.add(position)
                players_yet_to_act.discard(position)
                active_players = [p for p in active_players if p != position]
                
                # Check if only one player remains
                if len(active_players) <= 1:
                    # Process any remaining actions and end
                    while action_idx < len(all_actions):
                        remaining_pos, remaining_move = all_actions[action_idx]
                        if remaining_pos not in folded_players:
                            street_moves[current_street].append(remaining_move)
                        action_idx += 1
                    return street_moves
                    
            elif move in [MoveType.BET, MoveType.RAISE]:
                # Aggression - all other active players must respond
                last_aggressor_position = position
                players_yet_to_act = set(active_players) - {position}
                
            elif move in [MoveType.CALL, MoveType.CHECK]:
                # Passive action - remove from "need to act" list
                players_yet_to_act.discard(position)
            
            # Check if betting round is complete
            if not players_yet_to_act:
                # All players have acted appropriately
                betting_round_complete = True
            elif (last_aggressor_position is None and 
                  len(players_yet_to_act) == 0):
                # No aggression and all players acted (check-through)
                betting_round_complete = True
        
        # Move to next street if round completed and not on river
        if betting_round_complete and current_street_idx < 3:
            current_street_idx += 1
    
    return street_moves


def group_moves_by_street_simple(player_moves: Dict[Union[str, Position], List[Union[MoveType, str]]]) -> Dict[Street, List[MoveType]]:
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
                all_moves.append(move_type)

    current_street_idx = 0
    streets = [Street.PREFLOP, Street.FLOP, Street.TURN, Street.RIVER]
    consecutive_checks = 0
    last_was_aggressive = False

    for move in all_moves:
        current_street = streets[min(current_street_idx, 3)]
        street_moves[current_street].append(move)

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