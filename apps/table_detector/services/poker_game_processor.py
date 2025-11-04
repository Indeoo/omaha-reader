import os

from loguru import logger

from shared.domain.game_snapshot import GameSnapshot
from table_detector.domain.captured_window import CapturedWindow
from table_detector.domain.omaha_game import OmahaGame
from table_detector.services.game_format_service import GameFormatService
from table_detector.services.position_service import PositionService
from table_detector.utils.detect_utils import DetectUtils
from table_detector.utils.drawing_utils import save_detection_result


class PokerGameProcessor:

    def __init__(self):
        self.debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'

    def process_window(self, captured_image: CapturedWindow, timestamp_folder):
        """Process captured image and return formatted game data for transmission."""
        window_name = captured_image.window_name

        self.validate_image(captured_image)

        game_snapshot = PokerGameProcessor.create_game_snapshot(captured_image.get_cv2_image())
        if self.debug_mode:
            save_detection_result(timestamp_folder, captured_image, game_snapshot)

        return GameFormatService.game_to_dict(window_name, game_snapshot)

    def validate_image(self, captured_image: CapturedWindow):
        # Add size validation
        image_width, image_height = captured_image.get_size()
        if image_width != 784 or image_height != 584:
            raise ValueError(
                f"Неправильный размер картинки для окна {captured_image.window_name}. Ожидаеться: 784x584, Реальный размер: {image_width}x{image_height}. Скорее всего нужно поменять Jurojin Layout, размер окна в Jurojin должен быть: 770x577")

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