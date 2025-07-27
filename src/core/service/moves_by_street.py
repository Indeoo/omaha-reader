from typing import List, Union, Tuple, Dict


def group_moves_by_street(player_moves: Dict[str, List[Union[str, Tuple[str, float]]]]) -> Dict[str, List[str]]:
    """
    Groups player moves by street according to proper Omaha poker rules.
    
    Poker Rule: A betting round ends when action comes back to the last aggressor 
    and everyone has either called, folded, or (if no aggression) checked.
    
    Args:
        player_moves: Dict with position names as keys and lists of actions as values
                     Actions can be strings or tuples (action, amount)
    
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
    position_order = ['SB', 'BB', 'EP', 'MP', 'CO', 'BTN']
    
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
    
    while action_idx < len(all_actions) and current_street_idx < 4:
        current_street = streets[current_street_idx]
        
        # Determine active players for this street  
        active_players = [pos for pos in position_order 
                         if pos in player_moves and pos not in folded_players]
        
        if len(active_players) <= 1:
            break  # Game over
        
        # Process betting round for current street
        betting_round_over = False
        last_aggressor = None
        players_who_need_to_act = set(active_players)
        street_action_count = 0
        
        while action_idx < len(all_actions) and not betting_round_over:
            position, action = all_actions[action_idx]
            
            # Skip folded players
            if position in folded_players:
                action_idx += 1
                continue
            
            # Add action to current street
            street_moves[current_street].append(action)
            action_idx += 1
            street_action_count += 1
            
            # Update game state
            if action == "fold":
                folded_players.add(position)
                players_who_need_to_act.discard(position)
                active_players = [p for p in active_players if p != position]
                
                if len(active_players) <= 1:
                    betting_round_over = True
                    
            elif action in ["bet", "raise"]:
                last_aggressor = position
                # After aggression, all other active players need to respond
                players_who_need_to_act = set(active_players) - {position}
                
            elif action in ["call", "check"]:
                # This player has responded to current betting level
                players_who_need_to_act.discard(position)
                
                # Check if round is complete
                if not players_who_need_to_act:
                    # All players have acted appropriately
                    betting_round_over = True
        
        # Additional check: if we've processed actions for all active players
        # and there was no aggression, the round should end
        if (not betting_round_over and 
            last_aggressor is None and 
            street_action_count >= len(active_players)):
            betting_round_over = True
        
        # Move to next street
        if betting_round_over and current_street_idx < 3:
            current_street_idx += 1
    
    return street_moves


def group_moves_by_street_simple(player_moves: Dict[str, List[str]]) -> Dict[str, List[str]]:
    street_moves = {
        "preflop": [],
        "flop": [],
        "turn": [],
        "river": []
    }

    position_order = ['SB', 'BB', 'UTG', 'MP', 'CO', 'BTN']

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
            if consecutive_checks >= 2 and last_was_aggressive:
                current_street_idx = min(current_street_idx + 1, 3)
                consecutive_checks = 0
        elif move in ["bet", "raise"]:
            last_was_aggressive = True
            consecutive_checks = 0
        elif move == "call":
            consecutive_checks = 0

    return street_moves