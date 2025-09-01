from typing import Dict, List, Optional

from loguru import logger

from shared.domain.detection import Detection
from shared.domain.detected_position import DetectedPosition
from shared.domain.game_snapshot import GameSnapshot
from shared.domain.moves import MoveType
from shared.domain.position import Position
from table_detector.services.omaha_action_processor import group_moves_by_street
from table_detector.utils.detect_utils import DetectUtils


class GameSnapshotIncorrectException(Exception):
    pass


class GameSnapshotService:

    @staticmethod
    def create_game_snapshot(cv2_image):
        player_cards_detections = DetectUtils.detect_player_cards(cv2_image)
        table_cards_detections = DetectUtils.detect_table_cards(cv2_image)
        position_detections = DetectUtils.detect_positions(cv2_image)
        action_detections = DetectUtils.get_player_actions_detection(cv2_image)

        # Convert position detections to DetectedPosition enums first  
        detected_positions = GameSnapshotService._convert_detections_to_detected_positions(position_detections)
        
        # Filter valid positions and recover missing positions in a single pass
        recovered_positions = GameSnapshotService._filter_and_recover_positions(
            detected_positions,
            action_detections
        )
        
        position_actions = GameSnapshotService._convert_to_position_actions(action_detections, recovered_positions)

        moves = group_moves_by_street(position_actions)
        logger.info(moves)

        game_snapshot = (
            GameSnapshot
            .builder()
            .with_player_cards(player_cards_detections)
            .with_table_cards(table_cards_detections)
            .with_bids(None)
            .with_positions(recovered_positions)
            .with_actions(action_detections)
            .with_moves(moves)
            .build()
        )

        return game_snapshot


    @staticmethod
    def _infer_missing_position(player_id: int, detected_positions: Dict[int, Position]) -> Optional[str]:
        """
        Infer the most likely position for a player based on detected positions of other players.
        Uses poker table position logic and seating order.
        
        Args:
            player_id: The player whose position needs to be inferred
            detected_positions: Currently detected Position enums from other players
            
        Returns:
            Inferred position name or None if cannot be determined
        """
        if not detected_positions:
            return None

        # Extract detected position names
        detected_position_names = set()
        for position_enum in detected_positions.values():
            detected_position_names.add(position_enum.value)

        # Define common position sets for different table sizes
        position_sets = {
            6: ['EP', 'MP', 'CO', 'BTN', 'SB', 'BB'],
            5: ['EP', 'CO', 'BTN', 'SB', 'BB'],
            4: ['CO', 'BTN', 'SB', 'BB'],
            3: ['BTN', 'SB', 'BB'],
            2: ['SB', 'BB']
        }

        # Determine likely table size based on detected positions
        table_size = 6  # Default
        for size, positions in position_sets.items():
            if detected_position_names.issubset(set(positions)):
                table_size = size
                break

        # Find missing positions for this table size
        expected_positions = set(position_sets[table_size])
        missing_positions = expected_positions - detected_position_names

        # Simple heuristic: if only one position is missing, assign it
        if len(missing_positions) == 1:
            return list(missing_positions)[0]

        # More complex logic could be added here based on player_id and seating patterns
        # For now, return the most common missing position based on typical poker games
        priority_order = ['BTN', 'SB', 'BB', 'CO', 'EP', 'MP']
        for position in priority_order:
            if position in missing_positions:
                return position

        return None

    @staticmethod
    def _convert_detection_to_position(position_detection: Detection) -> Position:
        """
        Convert a Detection object to a Position enum.
        
        Args:
            position_detection: Detection object containing position information
            
        Returns:
            Position enum corresponding to the detection
            
        Raises:
            ValueError: If position cannot be normalized to a valid Position
        """
        position_name = position_detection.position_name
        
        if position_name == 'NO':
            raise ValueError("Invalid position 'NO'")
        
        # Clean up position name suffixes
        if position_name.endswith('_fold'):
            position_name = position_name[:-5]  # Remove exactly "_fold"
        elif position_name.endswith('_low'):
            position_name = position_name[:-4]  # Remove exactly "_low"
        elif position_name.endswith('_now'):
            position_name = position_name[:-4]  # Remove exactly "_now"
        
        # Convert position string to Position enum
        return Position.normalize_position(position_name)

    @staticmethod 
    def _convert_detections_to_detected_positions(positions: Dict[int, Detection]) -> Dict[int, DetectedPosition]:
        """
        Convert a dictionary of Detection objects to DetectedPosition enums.
        
        Args:
            positions: Dict mapping player_id to Detection objects
            
        Returns:
            Dict mapping player_id to DetectedPosition enums
        """
        converted_positions = {}
        
        for player_id, position_detection in positions.items():
            try:
                detected_position = DetectedPosition.from_detection_name(position_detection.name)
                converted_positions[player_id] = detected_position
            except ValueError as e:
                logger.warning(f"Skipping unknown detection '{position_detection.name}' for player {player_id}: {e}")
                continue
                
        return converted_positions

    @staticmethod
    def _filter_and_recover_positions(
            detected_positions: Dict[int, DetectedPosition],
            detected_actions: Dict[int, List[Detection]]
    ) -> Dict[int, Position]:
        """
        Filter DetectedPosition enums to valid positions and recover missing positions
        from action evidence in a single pass.
        
        Args:
            detected_positions: Dict mapping player_id to DetectedPosition enums
            detected_actions: Dict mapping player_id to list of action detections
            
        Returns:
            Dict mapping player_id to Position enums (direct positions + recovered positions)
        """
        result_positions = {}
        
        # Single pass: filter valid positions and recover from actions
        for player_id, detected_pos in detected_positions.items():
            if detected_pos.is_position():
                # Direct position conversion
                position_enum = detected_pos.to_position()
                if position_enum:
                    result_positions[player_id] = position_enum
                    logger.debug(f"Direct position for player {player_id}: {position_enum}")
                    
            elif detected_pos.is_action():
                # Immediate recovery attempt for action text
                inferred_position_string = GameSnapshotService._infer_missing_position(
                    player_id, result_positions
                )
                
                if inferred_position_string:
                    try:
                        inferred_position_enum = Position.normalize_position(inferred_position_string)
                        result_positions[player_id] = inferred_position_enum
                        logger.info(f"Recovered position for player {player_id}: {inferred_position_enum} (detected action: {detected_pos.value})")
                    except ValueError as e:
                        logger.warning(f"Failed to convert inferred position '{inferred_position_string}' for player {player_id}: {e}")
            
            # NO_POSITION is automatically ignored (neither is_position() nor is_action())
        
        # Second pass: check for additional recovery opportunities from regular action detections
        for player_id, action_list in detected_actions.items():
            if player_id in result_positions:
                continue  # Position already resolved
                
            if not action_list:
                continue  # No actions detected for this player
                
            # Check if any regular action detection contains poker keywords
            poker_action_keywords = [
                'limps', 'limp', 'calls', 'call', 'raises', 'raise', 'bets', 'bet',
                'folds', 'fold', 'checks', 'check', 'allin', 'all-in'
            ]
            
            has_poker_action = False
            for action in action_list:
                action_name_lower = action.name.lower()
                if any(keyword in action_name_lower for keyword in poker_action_keywords):
                    has_poker_action = True
                    break
                    
            if has_poker_action:
                inferred_position_string = GameSnapshotService._infer_missing_position(
                    player_id, result_positions
                )
                
                if inferred_position_string:
                    try:
                        inferred_position_enum = Position.normalize_position(inferred_position_string)
                        result_positions[player_id] = inferred_position_enum
                        logger.info(f"Recovered position for player {player_id}: {inferred_position_enum} (from regular actions)")
                    except ValueError as e:
                        logger.warning(f"Failed to convert inferred position '{inferred_position_string}' for player {player_id}: {e}")
        
        return result_positions

    @staticmethod
    def _convert_to_position_actions(actions, positions: Dict[int, Position]) -> Dict[Position, List[MoveType]]:
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
                if position_enum in result:
                    result[position_enum].extend(move_types)
                else:
                    result[position_enum] = move_types

        # Validate position continuity
        GameSnapshotService._validate_position_continuity(result)

        logger.info(result)

        return result

    @staticmethod
    def _determine_table_size(detected_positions: set[Position]) -> int:
        """
        Determine the most likely table size based on detected positions.
        
        Args:
            detected_positions: Set of detected Position enums
            
        Returns:
            Most likely table size (2-6 players)
        """
        position_count = len(detected_positions)

        # If we have MP, it's likely 6-max
        if Position.MIDDLE_POSITION in detected_positions:
            return 6

        # If we have EP but no MP, likely 5-max  
        if Position.EARLY_POSITION in detected_positions:
            return 5

        # If we have CO but no EP, likely 4-max
        if Position.CUTOFF in detected_positions:
            return 4

        # If we have BTN but no CO, likely 3-max
        if Position.BUTTON in detected_positions:
            return 3

        # If only blinds detected, likely 2-max (heads-up)
        if detected_positions.issubset({Position.SMALL_BLIND, Position.BIG_BLIND}):
            return 2

        # Fallback: estimate based on position count
        return min(max(position_count, 2), 6)

    @staticmethod
    def _get_valid_positions_for_table_size(table_size: int) -> set[Position]:
        """
        Get the valid positions for a given table size.
        
        Args:
            table_size: Number of players (2-6)
            
        Returns:
            Set of valid Position enums for that table size
        """
        position_sets = {
            2: {Position.SMALL_BLIND, Position.BIG_BLIND},  # Heads-up
            3: {Position.BUTTON, Position.SMALL_BLIND, Position.BIG_BLIND},
            4: {Position.CUTOFF, Position.BUTTON, Position.SMALL_BLIND, Position.BIG_BLIND},
            5: {Position.EARLY_POSITION, Position.CUTOFF, Position.BUTTON, Position.SMALL_BLIND, Position.BIG_BLIND},
            6: {Position.EARLY_POSITION, Position.MIDDLE_POSITION, Position.CUTOFF, Position.BUTTON,
                Position.SMALL_BLIND, Position.BIG_BLIND}
        }

        return position_sets.get(table_size, position_sets[6])  # Default to 6-max

    @staticmethod
    def _validate_position_continuity(position_actions: Dict[Position, List[MoveType]]) -> None:
        """
        Validate that detected positions are consistent with a valid table size configuration.
        
        Checks that the detected positions form a valid subset of positions for some
        table size (2-6 players), ensuring no impossible position combinations.
        
        Args:
            position_actions: Dict mapping Position enums to MoveType lists
        """
        if not position_actions:
            return

        detected_positions = set(position_actions.keys())

        # Determine the most likely table size
        table_size = GameSnapshotService._determine_table_size(detected_positions)
        valid_positions = GameSnapshotService._get_valid_positions_for_table_size(table_size)

        # Check if detected positions are a valid subset
        invalid_positions = detected_positions - valid_positions

        if invalid_positions:
            invalid_names = [pos.value for pos in invalid_positions]
            detected_names = [pos.value for pos in detected_positions]
            valid_names = [pos.value for pos in valid_positions]

            raise GameSnapshotIncorrectException(
                f"Invalid position combination detected for {table_size}-max table: "
                f"Detected positions {detected_names} include invalid positions {invalid_names}. "
                f"Valid positions for {table_size}-max are {valid_names}."
            )

        # Note: We don't validate for missing positions since this is partial detection
        # The main validation above ensures detected positions are valid for the table size
