from typing import List, Union, Tuple, Dict


def group_moves_by_street(player_moves: Dict[str, List[Union[str, Tuple[str, float]]]]) -> Dict[str, List[str]]:
    """
    Groups player moves by street according to proper Omaha poker rules.
    
    Omaha Poker Rules:
    - A betting round ends when all active players have either called the last raise, 
      folded, or (if no betting) checked
    - Blinds are posted automatically and not included in player_moves
    - Action order: EP, MP, CO, BTN, SB, BB (for voluntary actions)
    - Streets progress: preflop -> flop -> turn -> river
    
    Args:
        player_moves: Dict with position names as keys and lists of actions as values
                     Actions can be strings or tuples (action, amount)
                     Only voluntary actions, blinds excluded
    
    Returns:
        Dict with street names as keys and ordered lists of actions as values
    """
    if not player_moves:
        return {"preflop": [], "flop": [], "turn": [], "river": []}
    
    street_moves = {
        "preflop": [],
        "flop": [],
        "turn": [],
        "river": []
    }

    # Build chronological action sequence
    all_actions = []
    max_actions = max(len(moves) for moves in player_moves.values())
    
    # Correct action order for Omaha: EP acts first for voluntary actions
    # Preflop: EP, MP, CO, BTN, SB, BB (after blinds posted)
    # Postflop: SB, BB, EP, MP, CO, BTN (but only active players)
    position_order = ['EP', 'MP', 'CO', 'BTN', 'SB', 'BB']
    
    for action_idx in range(max_actions):
        for position in position_order:
            if position in player_moves and action_idx < len(player_moves[position]):
                action = player_moves[position][action_idx]
                action_str = action[0] if isinstance(action, tuple) else action
                all_actions.append((position, action_str))
    
    if not all_actions:
        return street_moves
    
    # State tracking
    streets = ["preflop", "flop", "turn", "river"]
    current_street_idx = 0
    action_idx = 0
    folded_players = set()
    
    # Process all actions, grouping by betting rounds
    while action_idx < len(all_actions) and current_street_idx < 4:
        current_street = streets[current_street_idx]
        
        # Determine active players for this street  
        active_players = [pos for pos in position_order 
                         if pos in player_moves and pos not in folded_players]
        
        # Process betting round for current street
        betting_round_over = False
        last_aggressor = None
        players_who_acted = set()
        # In Omaha, all active players must act at start of betting round
        players_who_need_to_respond = set(active_players)
        
        while action_idx < len(all_actions) and not betting_round_over:
            position, action = all_actions[action_idx]
            
            # Skip actions from folded players
            if position in folded_players:
                action_idx += 1
                continue
            
            # Add action to current street
            street_moves[current_street].append(action)
            action_idx += 1
            players_who_acted.add(position)
            
            # Update game state based on action
            if action == "fold":
                folded_players.add(position)
                players_who_need_to_respond.discard(position)
                active_players = [p for p in active_players if p != position]
                
                # Check if game is over (only one player left)
                if len(active_players) <= 1:
                    # Process any remaining actions for completeness
                    while action_idx < len(all_actions):
                        remaining_pos, remaining_action = all_actions[action_idx]
                        if remaining_pos not in folded_players:
                            action_str = remaining_action[0] if isinstance(remaining_action, tuple) else remaining_action
                            street_moves[current_street].append(action_str)
                        action_idx += 1
                    return street_moves
                    
            elif action in ["bet", "raise"]:
                # Aggression: all other active players must respond
                last_aggressor = position
                players_who_need_to_respond = set(active_players) - {position}
                
            elif action in ["call", "check"]:
                # Player has responded to current betting level
                players_who_need_to_respond.discard(position)
            
            # Check if betting round is complete
            if _is_betting_round_complete(active_players, players_who_acted, 
                                        players_who_need_to_respond, last_aggressor):
                betting_round_over = True
        
        # Move to next street if betting round completed and not on river
        if betting_round_over and current_street_idx < 3:
            current_street_idx += 1
    
    return street_moves


def _is_betting_round_complete(active_players: List[str], players_who_acted: set, 
                              players_who_need_to_respond: set, last_aggressor: str) -> bool:
    """
    Determines if a betting round is complete according to Omaha poker rules.
    
    A betting round is complete when:
    1. All active players who need to respond have done so, OR
    2. All active players have acted and there was no aggression (all checked)
    """
    # Case 1: Everyone who needed to respond has done so
    if not players_who_need_to_respond:
        return True
    
    # Case 2: No aggression and all active players have acted (check-through)
    if last_aggressor is None and len(players_who_acted) >= len(active_players):
        return True
    
    return False


def group_moves_by_street_simple(player_moves: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Simple approach to group moves by street.
    Uses consistent position order and basic street transition logic.
    """
    street_moves = {
        "preflop": [],
        "flop": [],
        "turn": [],
        "river": []
    }

    # Use same position order as main function for consistency
    position_order = ['EP', 'MP', 'CO', 'BTN', 'SB', 'BB']

    all_moves = []
    for position in position_order:
        if position in player_moves:
            all_moves.extend(player_moves[position])

    current_street_idx = 0
    streets = ["preflop", "flop", "turn", "river"]
    consecutive_checks = 0
    last_was_aggressive = False

    for move in all_moves:
        current_street = streets[min(current_street_idx, 3)]
        street_moves[current_street].append(move)

        if move in ["check"]:
            consecutive_checks += 1
            if consecutive_checks >= 2 and not last_was_aggressive:
                current_street_idx = min(current_street_idx + 1, 3)
                consecutive_checks = 0
                last_was_aggressive = False
        elif move in ["bet", "raise"]:
            last_was_aggressive = True
            consecutive_checks = 0
        elif move == "call":
            consecutive_checks = 0
            # After calls, if last_was_aggressive, round might end
            if last_was_aggressive:
                current_street_idx = min(current_street_idx + 1, 3)
                last_was_aggressive = False
        elif move == "fold":
            consecutive_checks = 0

    return street_moves