from pathlib import Path

import cv2


def load_image(image_name):
    test_dir = Path(__file__).parent.parent
    test_image_path = test_dir / "resources" / "service" / "poker_game_processor" / image_name

    return cv2.imread(str(test_image_path))