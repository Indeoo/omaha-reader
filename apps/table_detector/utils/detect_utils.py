from typing import List, Dict

import numpy as np
from loguru import logger

from shared.domain.detection import Detection
from table_detector.utils.opencv_utils import coords_to_search_region
from table_detector.services.template_matcher_service import TemplateMatchService

ACTION_POSITIONS = {
    1: (300, 430, 200, 30),  # Bottom center (hero)
    2: (10, 400, 200, 30),  # Left side
    3: (25, 120, 200, 30),  # Top left
    4: (315, 80, 200, 30),  # Top center
    5: (580, 130, 200, 30),  # Top right
    6: (580, 380, 200, 30),  # Right side
}


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
                    else:
                        player_positions[player_num] = Detection("NO", None, None, 1)

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
    def detect_player_cards(cv2_image) -> List[Detection]:
        return TemplateMatchService.find_player_cards(cv2_image)

    @staticmethod
    def detect_table_cards(cv2_image) -> List[Detection]:
        return TemplateMatchService.find_table_cards(cv2_image)

    @staticmethod
    def get_player_actions_detection(image: np.ndarray) -> Dict[int, List[Detection]]:
        player_actions = {}

        for player_id, region in ACTION_POSITIONS.items():
            search_region = coords_to_search_region(
                x=region[0],
                y=region[1],
                w=region[2],
                h=region[3],
            )

            actions = TemplateMatchService.find_jurojin_actions(image, search_region=search_region)
            player_actions[player_id] = actions

        return player_actions
