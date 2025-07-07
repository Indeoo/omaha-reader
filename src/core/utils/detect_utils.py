from typing import List, Dict

import numpy as np
from loguru import logger

from src.core.domain.captured_window import CapturedWindow
from src.core.domain.detection_result import GameSnapshot
from src.core.domain.readed_card import ReadedCard
from src.core.service.matcher.player_action_matcher import PlayerActionMatcher
from src.core.service.matcher.player_card_matcher import PlayerCardMatcher
from src.core.service.matcher.player_position_matcher import DetectedPosition, PlayerPositionMatcher
from src.core.service.matcher.table_card_matcher import OmahaTableCard
from src.core.service.template_registry import TemplateRegistry
from src.core.utils.opencv_utils import draw_detected_positions, save_opencv_image, draw_detected_bids, \
    draw_detected_cards, coords_to_search_region


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
        self.template_registry = TemplateRegistry(country, project_root)

        self._player_move_reader = None
        self._player_move_reader = PlayerActionMatcher(self.template_registry.action_templates)
        self._player_position_readers = {}
        self._init_all_player_position_readers()


    def _init_all_player_position_readers(self):
        if not self.template_registry.has_position_templates():
            return

        try:
            for player_num, coords in PLAYER_POSITIONS.items():
                search_region = coords_to_search_region(
                    x=coords['x'] - POSITION_MARGIN,
                    y=coords['y'] - POSITION_MARGIN,
                    w=coords['w'] + 2 * POSITION_MARGIN,
                    h=coords['h'] + 2 * POSITION_MARGIN,
                    image_width=IMAGE_WIDTH,
                    image_height=IMAGE_HEIGHT
                )

                reader = PlayerPositionMatcher(self.template_registry.position_templates)
                reader.search_region = search_region
                self._player_position_readers[player_num] = reader

                logger.info(f"✅ Player {player_num} position reader initialized with search region: {search_region}")
        except Exception as e:
            logger.error(f"❌ Error initializing player position readers: {str(e)}")

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
                    result_image = self.draw_cards(result_image, table_cards,
                                              color=(0, 0, 255))
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

    def draw_cards(self, image: np.ndarray, readed_cards: List[ReadedCard], color=(0, 255, 0)) -> np.ndarray:
        detections = []
        for card in readed_cards:
            detection = {
                'template_name': card.template_name,
                'match_score': card.match_score,
                'bounding_rect': card.bounding_rect,
                'center': card.center,
                'scale': card.scale
            }
            detections.append(detection)

        return draw_detected_cards(
            image=image,
            detections=detections,
            color=color,
            thickness=2,
            font_scale=0.6,
            show_scale=True
        )

    def detect_player_cards(self, cv2_image) -> List[ReadedCard]:
        return PlayerCardMatcher(
            self.template_registry.player_templates,
            PlayerCardMatcher.DEFAULT_SEARCH_REGION
        ).read(cv2_image)

    def detect_table_cards(self, cv2_image) -> List[ReadedCard]:
        return OmahaTableCard(self.template_registry.table_templates, None).read(cv2_image)

    def detect_positions(self, cv2_image) -> Dict[int, DetectedPosition]:
        if not self.template_registry.has_position_templates() or not self._player_position_readers:
            return {}

        try:
            player_positions = {}

            for player_num, reader in self._player_position_readers.items():
                try:
                    detected_positions = reader.read(cv2_image)

                    if detected_positions:
                        best_position = detected_positions[0]
                        player_positions[player_num] = best_position

                except Exception as e:
                    logger.error(f"❌ Error checking player {player_num} position: {str(e)}")

            logger.info(f"    ✅ Found positions:")
            for player_num, position_result in player_positions.items():
                position = position_result.position_name
                logger.info(f"        P{player_num}: {position}")

            return player_positions

        except Exception as e:
            logger.error(f"❌ Error detecting positions: {str(e)}")
            return {}

    def detect_actions(self, cv2_image, window_name: str = "") -> List:
        try:
            detected_moves = self._player_move_reader.read(cv2_image)

            if detected_moves:
                move_types = [move.move_type for move in detected_moves]
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
