from typing import List, Dict
from loguru import logger
from src.core.service.template_matcher_service import Detection, TemplateMatchService, MatchConfig
from src.core.utils.opencv_utils import coords_to_search_region

PLAYER_POSITIONS = {
    1: {'x': 300, 'y': 375, 'w': 40, 'h': 40},
    2: {'x': 35, 'y': 330, 'w': 40, 'h': 40},
    3: {'x': 35, 'y': 173, 'w': 40, 'h': 40},
    4: {'x': 297, 'y': 120, 'w': 40, 'h': 40},
    5: {'x': 562, 'y': 168, 'w': 40, 'h': 40},
    6: {'x': 565, 'y': 332, 'w': 40, 'h': 40}
}

POSITION_MARGIN = 10

IMAGE_WIDTH = 784
IMAGE_HEIGHT = 584


class DetectUtils:
    @staticmethod
    def detect_positions(cv2_image) -> Dict[int, Detection]:
        try:
            player_positions = {}

            for player_num, coords in PLAYER_POSITIONS.items():
                search_region = coords_to_search_region(coords['x'], coords['y'], coords['w'], coords['h'])

                try:
                    detected_positions = TemplateMatchService.find_positions(cv2_image, search_region)

                    if detected_positions:
                        best_position = detected_positions[0]
                        player_positions[player_num] = best_position

                except Exception as e:
                    logger.error(f"❌ Error checking player {player_num} position: {str(e)}")

            logger.info(f"    ✅ Found positions:")
            for player_num, position in player_positions.items():
                logger.info(f"        P{player_num}: {position.name}")

            return player_positions

        except Exception as e:
            logger.error(f"❌ Error detecting positions: {str(e)}")
            return {}

    @staticmethod
    def detect_actions(cv2_image, window_name: str = "") -> List[Detection]:
        try:
            detected_moves = TemplateMatchService.find_actions(cv2_image)

            if detected_moves:
                move_types = [move.name for move in detected_moves]
                if window_name:
                    logger.info(f"🎯 Player's move detected in {window_name}! Options: {', '.join(move_types)}")
                return detected_moves
            else:
                if window_name:
                    logger.info(f"⏸️ Not player's move in {window_name} - no action buttons detected")
                return []

        except Exception as e:
            logger.error(f"❌ Error detecting moves: {str(e)}")
            return []
