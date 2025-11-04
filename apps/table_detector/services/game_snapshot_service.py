from typing import Dict, List, Tuple

from loguru import logger

from shared.domain.game_snapshot import GameSnapshot
from shared.domain.moves import MoveType
from shared.domain.position import Position
from table_detector.domain.omaha_game import OmahaGame
from table_detector.services.position_service import PositionService
from table_detector.utils.detect_utils import DetectUtils


class GameSnapshotService:

    @staticmethod
    def create_game_snapshot(cv2_image):
        player_cards_detections = DetectUtils.detect_player_cards(cv2_image)
        table_cards_detections = DetectUtils.detect_table_cards(cv2_image)
        position_detections = DetectUtils.detect_positions(cv2_image)
        action_detections = DetectUtils.get_player_actions_detection(cv2_image)

        recovered_positions = PositionService.get_positions(position_detections)

        position_actions = GameSnapshotService._convert_to_position_actions(action_detections, recovered_positions)

        game = OmahaGame(len(position_actions))
        game.simulate_all_moves(position_actions)
        moves = game.get_moves_by_street()
        logger.info(moves)

        game_snapshot = (
            GameSnapshot
            .builder()
            .with_player_cards(player_cards_detections)
            .with_table_cards(table_cards_detections)
            .with_bids(None)
            .with_positions(position_detections)
            .with_actions(action_detections)
            .with_moves(moves)
            .build()
        )

        return game_snapshot

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

        logger.info(result)

        return result
