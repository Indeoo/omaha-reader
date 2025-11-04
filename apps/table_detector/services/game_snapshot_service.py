from typing import Dict, List, Tuple

from loguru import logger

from shared.domain.game_snapshot import GameSnapshot
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

        position_actions = OmahaGame._convert_to_position_actions(action_detections, recovered_positions)
        game = OmahaGame(len(position_actions))
        game.simulate_all_moves(position_actions)
        moves = game.get_moves_by_street()
        logger.info(moves)

        game_snapshot = (
            GameSnapshot
            .builder()
            .with_player_cards(player_cards_detections)
            .with_table_cards(table_cards_detections)
            .with_positions(position_detections)
            .with_actions(action_detections)
            .with_moves(moves)
            .build()
        )

        return game_snapshot