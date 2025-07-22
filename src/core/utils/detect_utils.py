from typing import List, Dict

import numpy as np
from loguru import logger

from src.core.domain.captured_window import CapturedWindow
from src.core.domain.detection_result import GameSnapshot
from src.core.service.template_matcher_service import Detection, TemplateMatchService, MatchConfig
from src.core.utils.opencv_utils import draw_detected_positions, save_opencv_image, draw_detected_bids, \
    draw_detected_cards


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
    def __init__(
            self,
            country: str = "canada",
            project_root: str = None,
    ):
        #self.template_registry = TemplateRegistry(country, project_root)
        self._position_search_regions = {}
    #     self._init_position_search_regions()
    #
    # def _init_position_search_regions(self):
    #     if not self.template_registry.has_position_templates():
    #         return
    #
    #     try:
    #         for player_num, coords in PLAYER_POSITIONS.items():
    #             search_region = coords_to_search_region(
    #                 x=coords['x'] - POSITION_MARGIN,
    #                 y=coords['y'] - POSITION_MARGIN,
    #                 w=coords['w'] + 2 * POSITION_MARGIN,
    #                 h=coords['h'] + 2 * POSITION_MARGIN,
    #                 image_width=IMAGE_WIDTH,
    #                 image_height=IMAGE_HEIGHT
    #             )
    #             self._position_search_regions[player_num] = search_region
    #             logger.info(f"✅ Player {player_num} position search region: {search_region}")
    #     except Exception as e:
    #         logger.error(f"❌ Error initializing position search regions: {str(e)}")

    def save_detection_result_image(self, timestamp_folder: str, captured_image: CapturedWindow, game_snapshot: GameSnapshot):
        window_name = captured_image.window_name
        filename = captured_image.filename

        try:
            cv2_image = captured_image.get_cv2_image()
            result_image = cv2_image.copy()

            drawn_items = []

            has_cards = game_snapshot.has_cards
            player_cards = game_snapshot.player_cards
            table_cards = game_snapshot.table_cards
            positions = game_snapshot.positions
            bids = game_snapshot.bids

            if has_cards:
                if player_cards:
                    result_image = self.draw_cards(result_image, player_cards, color=(0, 255, 0))
                    drawn_items.append(f"{len(player_cards)} player cards")

                if table_cards:
                    result_image = self.draw_cards(result_image, table_cards, color=(0, 0, 255))
                    drawn_items.append(f"{len(table_cards)} table cards")

            if positions:
                result_image = draw_detected_positions(result_image, positions.values())
                drawn_items.append(f"{len(positions)} positions")

            if bids:
                result_image = draw_detected_bids(result_image, bids)
                drawn_items.append(f"{len(bids)} bids")

            result_filename = filename.replace('.png', '_result.png')
            save_opencv_image(result_image, timestamp_folder, result_filename)

            if drawn_items:
                logger.info(f"    📷 Saved {result_filename} with: {', '.join(drawn_items)}")
            else:
                logger.info(f"    📷 Saved {result_filename} (no detections)")

        except Exception as e:
            logger.error(f"    ❌ Error saving result image for {window_name}: {str(e)}")

    def draw_cards(self, image: np.ndarray, detections: List[Detection], color=(0, 255, 0)) -> np.ndarray:
        detection_dicts = []
        for detection in detections:
            detection_dict = {
                'template_name': detection.name,
                'match_score': detection.match_score,
                'bounding_rect': detection.bounding_rect,
                'center': detection.center,
                'scale': detection.scale
            }
            detection_dicts.append(detection_dict)

        return draw_detected_cards(
            image=image,
            detections=detection_dicts,
            color=color,
            thickness=2,
            font_scale=0.6,
            show_scale=True
        )

    def detect_player_cards(self, cv2_image) -> List[Detection]:
        return TemplateMatchService.find_player_cards(cv2_image)

    def detect_table_cards(self, cv2_image) -> List[Detection]:
        return TemplateMatchService.find_table_cards(cv2_image)

    def detect_positions(self, cv2_image) -> Dict[int, Detection]:
        try:
            player_positions = {}

            for player_num, search_region in self._position_search_regions.items():
                try:
                    config = MatchConfig(
                        search_region=search_region,
                        threshold=0.99,
                        min_size=15,
                        sort_by='score'
                    )
                    detected_positions = TemplateMatchService.find_matches(cv2_image, config)

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

    def detect_actions(self, cv2_image, window_name: str = "") -> List[Detection]:
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