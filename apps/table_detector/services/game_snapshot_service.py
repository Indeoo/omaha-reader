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

                    if move_types:  # Only add if we have valid moves
                        result[position_enum] = move_types

                except ValueError as e:
                    logger.warning(f"Skipping invalid position '{position_name}': {e}")
                    continue

        # Validate position continuity
        GameSnapshotService._validate_position_continuity(result)

        logger.info(result)

        return result

    @staticmethod
    def _validate_position_continuity(position_actions: Dict[Position, List[MoveType]]) -> None:
        """
        Validate position continuity in the action sequence to detect potential gaps.
        
        Checks for scenarios where later positions have actions but earlier positions
        in the action order are missing, which could indicate incomplete detection.
        
        Args:
            position_actions: Dict mapping Position enums to MoveType lists
        """
        if not position_actions:
            return

        detected_positions = set(position_actions.keys())
        action_order = Position.get_action_order()

        # Find the range of positions that should be active
        detected_indices = [action_order.index(pos) for pos in detected_positions]
        if not detected_indices:
            return

        min_idx = min(detected_indices)
        max_idx = max(detected_indices)

        # Check for gaps in the position sequence
        expected_positions = set(action_order[min_idx:max_idx + 1])
        missing_positions = expected_positions - detected_positions

        if missing_positions:
            missing_names = [pos.value for pos in missing_positions]
            detected_names = [pos.value for pos in detected_positions]

            raise GameSnapshotIncorrectException(
                f"Position continuity issue detected: "
                f"Missing positions {missing_names} between detected positions {detected_names}. "
                f"This may indicate incomplete action detection and could affect game reconstruction."
            )
