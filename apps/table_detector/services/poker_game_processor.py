import os

from table_detector.domain.captured_window import CapturedWindow
from table_detector.services.game_format_service import GameFormatService
from table_detector.services.game_snapshot_service import GameSnapshotService
from table_detector.utils.drawing_utils import save_detection_result


class PokerGameProcessor:

    def __init__(self):
        self.debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'

    def process_window(self, captured_image: CapturedWindow, timestamp_folder):
        """Process captured image and return formatted game data for transmission."""
        window_name = captured_image.window_name

        self.validate_image(captured_image)

        game_snapshot = GameSnapshotService.create_game_snapshot(captured_image.get_cv2_image())
        if self.debug_mode:
            save_detection_result(timestamp_folder, captured_image, game_snapshot)

        return GameFormatService.game_to_dict(window_name, game_snapshot)

    def validate_image(self, captured_image: CapturedWindow):
        # Add size validation
        image_width, image_height = captured_image.get_size()
        if image_width != 784 or image_height != 584:
            raise ValueError(
                f"Неправильный размер картинки для окна {captured_image.window_name}. Ожидаеться: 784x584, Реальный размер: {image_width}x{image_height}. Скорее всего нужно поменять Jurojin Layout, размер окна в Jurojin должен быть: 770x577")
