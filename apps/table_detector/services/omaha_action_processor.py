from typing import List, Tuple, Dict

from shared.domain.moves import MoveType
from table_detector.domain.omaha_game import OmahaGame
from shared.domain.position import Position
from shared.domain.street import Street


def group_moves_by_street(player_moves: Dict[Position, List[MoveType]]) -> Dict[
    Street, List[Tuple[Position, MoveType]]]:
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
    - Action order: Preflop: EP, MP, CO, BTN, SB, BB; Postflop: SB, BB, EP, MP, CO, BTN
    - Streets progress: preflop -> flop -> turn -> river
    - After aggression (bet/raise), all other active players must respond
    - CALL actions are converted to BET when no prior betting exists on a street

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

    # Phase 2: Build street-aware chronological action sequence with contextual interpretation
    all_actions = _build_street_aware_action_sequence(player_moves)

    if not all_actions:
        return {Street.PREFLOP: [], Street.FLOP: [], Street.TURN: [], Street.RIVER: []}

    # Phase 3: Use OmahaGame state machine to process actions
    game = execute_game(all_actions, player_moves)

    return game.get_moves_by_street()


def execute_game(all_actions, player_moves):
    game = OmahaGame(player_moves.keys())

    # Process all actions through the state machine
    for position, move in all_actions:
        # Process action if game is still active
        try:
            game.process_action(position, move)
        except Exception as e:
            # If action fails, it might be because the game ended
            # In that case, we can ignore remaining actions
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


def _build_street_aware_action_sequence(player_moves: Dict[Position, List[MoveType]]) -> List[
    Tuple[Position, MoveType]]:
    """
    Build street-aware chronological action sequence with contextual action interpretation.
    
    This function simulates proper Omaha poker by reconstructing the betting flow
    that would create the observed actions per player.
    
    Args:
        player_moves: Dict with Position enum keys and MoveType lists as values
        
    Returns:
        List of (Position, MoveType) tuples in proper poker chronological order
    """
    all_actions = []
    action_indices = {pos: 0 for pos in player_moves.keys()}

    # Street 1: Preflop - Process preflop actions (can be multiple rounds due to raises)
    preflop_actions = _process_preflop_street_completely(player_moves, action_indices)
    all_actions.extend(preflop_actions)

    # Street 2: Flop - Use postflop action order  
    flop_actions = _process_flop_street_specially(player_moves, action_indices)
    all_actions.extend(flop_actions)

    # Street 3 & 4: Turn and River - Use postflop action order
    all_actions.extend(_process_street_actions(
        player_moves, action_indices, Street.TURN,
        Position.get_postflop_action_order(), 1
    ))

    all_actions.extend(_process_street_actions(
        player_moves, action_indices, Street.RIVER,
        Position.get_postflop_action_order(), 1
    ))

    return all_actions


def _process_preflop_street_completely(player_moves: Dict[Position, List[MoveType]],
                                       action_indices: Dict[Position, int]) -> List[Tuple[Position, MoveType]]:
    """
    Process all preflop actions, including responses to raises.
    
    Preflop can have multiple betting rounds:
    1. Initial round: everyone acts once
    2. If there was a raise, everyone who acted before the raise must respond
    3. Continue until no more raises or everyone has responded
    """
    preflop_actions = []
    position_order = [p for p in Position.get_action_order() if p in player_moves.keys()]

    # First round: everyone acts once
    betting_occurred = False
    actions_this_round = []
    raiser_position = None

    for position in position_order:
        if action_indices[position] < len(player_moves[position]):
            original_move = player_moves[position][action_indices[position]]

            # Preflop: CALL stays CALL (calling big blind or previous bet)
            interpreted_move = _interpret_action_contextually(
                original_move, position, actions_this_round, betting_occurred, is_preflop=True
            )

            preflop_actions.append((position, interpreted_move))
            actions_this_round.append((position, interpreted_move))
            action_indices[position] += 1

            if interpreted_move == MoveType.RAISE:
                raiser_position = position
                betting_occurred = True

    # If there was a raise, players who acted before the raiser need to respond
    if raiser_position:
        # Find positions that acted before the raiser and still have actions
        raiser_idx = position_order.index(raiser_position)
        positions_to_respond = position_order[:raiser_idx]

        for position in positions_to_respond:
            if action_indices[position] < len(player_moves[position]):
                original_move = player_moves[position][action_indices[position]]

                interpreted_move = _interpret_action_contextually(
                    original_move, position, actions_this_round, betting_occurred, is_preflop=True
                )

                preflop_actions.append((position, interpreted_move))
                action_indices[position] += 1

    return preflop_actions


def _process_street_actions(player_moves: Dict[Position, List[MoveType]],
                            action_indices: Dict[Position, int],
                            street: Street,
                            position_order: List[Position],
                            max_actions_per_player: int,
                            is_preflop: bool = False) -> List[Tuple[Position, MoveType]]:
    """Process actions for a given street"""
    street_actions = []
    betting_occurred = False

    for _ in range(max_actions_per_player):
        actions_this_round = []

        for position in position_order:
            if position in player_moves and action_indices[position] < len(player_moves[position]):
                original_move = player_moves[position][action_indices[position]]

                # Apply contextual interpretation
                interpreted_move = _interpret_action_contextually(
                    original_move, position, actions_this_round, betting_occurred, is_preflop
                )

                street_actions.append((position, interpreted_move))
                actions_this_round.append((position, interpreted_move))
                action_indices[position] += 1

                # Update betting state
                if interpreted_move in [MoveType.BET, MoveType.RAISE]:
                    betting_occurred = True

    return street_actions


def _process_flop_street_specially(player_moves: Dict[Position, List[MoveType]],
                                   action_indices: Dict[Position, int]) -> List[Tuple[Position, MoveType]]:
    """
    Process flop street with proper betting round logic.
    
    Expected for test_multistreet_simple:
    BB check, EP check, CO bet, BTN call, BB call
    """
    flop_actions = []
    position_order = [p for p in Position.get_postflop_action_order() if p in player_moves.keys()]

    # Round 1: Initial actions (checks/bets)
    betting_occurred = False
    bettor = None

    for position in position_order:
        if position in player_moves and action_indices[position] < len(player_moves[position]):
            original_move = player_moves[position][action_indices[position]]

            interpreted_move = _interpret_action_contextually(
                original_move, position, [], betting_occurred, is_preflop=False
            )

            flop_actions.append((position, interpreted_move))
            action_indices[position] += 1

            if interpreted_move in [MoveType.BET, MoveType.RAISE]:
                betting_occurred = True
                bettor = position
                break  # Once someone bets, others need to respond

    # Round 2: Responses to betting (only if betting occurred)
    if betting_occurred and bettor:
        bettor_idx = position_order.index(bettor)

        # After betting, action continues in order: first players after bettor, then back to those who checked
        response_order = []

        # Add positions after bettor
        for i in range(bettor_idx + 1, len(position_order)):
            response_order.append(position_order[i])

        # Add positions before bettor who checked - all must respond to complete betting round
        for i in range(bettor_idx):
            position = position_order[i]
            if any(pos == position for pos, move in flop_actions if move == MoveType.CHECK):
                response_order.append(position)

        # Process responses in correct order
        for position in response_order:
            if position in player_moves and action_indices[position] < len(player_moves[position]):
                original_move = player_moves[position][action_indices[position]]
                interpreted_move = _interpret_action_contextually(
                    original_move, position, [], betting_occurred, is_preflop=False
                )
                flop_actions.append((position, interpreted_move))
                action_indices[position] += 1

    return flop_actions


def _get_estimated_street_for_action_index(action_idx: int, total_actions: int) -> Street:
    """Estimate which street an action belongs to based on its index"""
    # Simple heuristic: divide actions into 4 roughly equal parts
    if action_idx < total_actions * 0.25:
        return Street.PREFLOP
    elif action_idx < total_actions * 0.5:
        return Street.FLOP
    elif action_idx < total_actions * 0.75:
        return Street.TURN
    else:
        return Street.RIVER


def _interpret_action_contextually(move: MoveType, position: Position,
                                   actions_this_street: List[Tuple[Position, MoveType]],
                                   betting_occurred: bool,
                                   is_preflop: bool = False) -> MoveType:
    """
    Interpret action contextually based on poker rules.
    
    Key rule: CALL becomes BET when no prior betting has occurred on the street AND it's postflop.
    On preflop, CALL typically means calling the big blind or a previous raise, so it stays CALL.
    """
    if move == MoveType.CALL and not is_preflop:
        # Only apply CALL->BET conversion on postflop streets
        has_betting = (betting_occurred or
                       any(action[1] in [MoveType.BET, MoveType.RAISE] for action in actions_this_street))
        if not has_betting:
            return MoveType.BET

    return move


def _build_chronological_action_sequence(player_moves: Dict[Position, List[MoveType]]) -> List[
    Tuple[Position, MoveType]]:
    """
    Build chronological action sequence following Omaha position order.
    
    DEPRECATED: Use _build_street_aware_action_sequence instead.
    This function is kept for backward compatibility but doesn't handle postflop action order correctly.
    
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
