from typing import Dict, List

from loguru import logger

from shared.domain.game_snapshot import GameSnapshot
from shared.domain.moves import MoveType
from shared.domain.position import Position
from table_detector.services.omaha_action_processor import group_moves_by_street
from table_detector.services.template_matcher_service import TemplateMatchService
from table_detector.utils.detect_utils import DetectUtils

class GameSnapshotIncorrectException(Exception):
    pass

class GameSnapshotService:

    @staticmethod
    def create_game_snapshot(cv2_image):
        detected_player_cards = TemplateMatchService.find_player_cards(cv2_image)
        detected_table_cards = TemplateMatchService.find_table_cards(cv2_image)
        detected_positions = DetectUtils.detect_positions(cv2_image)
        detected_actions = DetectUtils.get_player_actions_detection(cv2_image)
        position_actions = GameSnapshotService._convert_to_position_actions(detected_actions, detected_positions)

        moves = group_moves_by_street(position_actions)
        logger.info(moves)

        game_snapshot = (
            GameSnapshot
            .builder()
            .with_player_cards(detected_player_cards)
            .with_table_cards(detected_table_cards)
            .with_bids(None)
            .with_positions(detected_positions)
            .with_actions(detected_actions)
            .with_moves(moves)
            .build()
        )

        return game_snapshot

    @staticmethod
    def _convert_to_position_actions(actions, positions) -> Dict[Position, List[MoveType]]:
        result = {}

        # First, add all detected positions to the result (even without actions)
        for player_id, position_data in positions.items():
            position_name = position_data.position_name

            if position_name == 'NO':
                continue

            # Clean up position name suffixes
            if position_name.endswith('_fold'):
                position_name = position_name[:-5]  # Remove exactly "_fold"
            elif position_name.endswith('_low'):
                position_name = position_name[:-4]  # Remove exactly "_low"
            elif position_name.endswith('_now'):
                position_name = position_name[:-4]  # Remove exactly "_now"

            try:
                # Convert position string to Position enum
                position_enum = Position.normalize_position(position_name)
                # Initialize with empty action list
                result[position_enum] = []
            except ValueError as e:
                logger.warning(f"Skipping invalid position '{position_name}': {e}")
                continue

        # Then, process actual actions for players that have them
        for player_id, detection_list in actions.items():
            if player_id in positions:
                position_name = positions[player_id].position_name

                if position_name == 'NO':
                    continue

                if position_name.endswith('_fold'):
                    position_name = position_name[:-5]  # Remove exactly "_fold"
                elif position_name.endswith('_low'):
                    position_name = position_name[:-4]  # Remove exactly "_low"
                elif position_name.endswith('_now'):
                    position_name = position_name[:-4]  # Remove exactly "_now"

                try:
                    # Convert position string to Position enum
                    position_enum = Position.normalize_position(position_name)

                    # Convert detection names to MoveType enums
                    move_types = []
                    for d in detection_list:
                        try:
                            move_type = MoveType.normalize_action(d.name)
                            move_types.append(move_type)
                        except ValueError as e:
                            logger.warning(f"Skipping invalid move '{d.name}' for position {position_name}: {e}")
                            continue

                    # Add moves to the existing position (which may already be initialized with empty list)
                    if position_enum in result:
                        result[position_enum].extend(move_types)
                    else:
                        result[position_enum] = move_types

                except ValueError as e:
                    logger.warning(f"Skipping invalid position '{position_name}': {e}")
                    continue

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
            6: {Position.EARLY_POSITION, Position.MIDDLE_POSITION, Position.CUTOFF, Position.BUTTON, Position.SMALL_BLIND, Position.BIG_BLIND}
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
