from typing import List, Dict, Union

import numpy as np

from src.core.domain.readed_card import ReadedCard
from src.core.domain.detection_result import DetectionResult
from src.core.domain.captured_image import CapturedImage
from src.core.utils.opencv_utils import save_opencv_image, draw_detected_cards, draw_detected_positions


def save_detection_result_image(timestamp_folder: str, captured_image: CapturedImage, result: Union[Dict, DetectionResult]):
    window_name = captured_image.window_name
    filename = captured_image.filename

    try:
        cv2_image = captured_image.get_cv2_image()
        result_image = cv2_image.copy()

        drawn_items = []

        if isinstance(result, DetectionResult):
            has_cards = result.has_cards
            player_cards = result.player_cards
            table_cards = result.table_cards
            positions = result.positions
        else:
            has_cards = result['has_cards']
            player_cards = result.get('player_cards', [])
            table_cards = result.get('table_cards', [])
            positions = result.get('positions', [])

        if has_cards:
            if player_cards:
                result_image = draw_cards(result_image, player_cards, color=(0, 255, 0))
                drawn_items.append(f"{len(player_cards)} player cards")

            if table_cards:
                result_image = draw_cards(result_image, table_cards,
                                          color=(0, 0, 255))
                drawn_items.append(f"{len(table_cards)} table cards")

        if positions:
            result_image = draw_detected_positions(result_image, positions)
            drawn_items.append(f"{len(positions)} positions")

        result_filename = filename.replace('.png', '_result.png')
        save_opencv_image(result_image, timestamp_folder, result_filename)

        if drawn_items:
            print(f"    📷 Saved {result_filename} with: {', '.join(drawn_items)}")
        else:
            print(f"    📷 Saved {result_filename} (no detections)")

    except Exception as e:
        print(f"    ❌ Error saving result image for {window_name}: {str(e)}")


def draw_cards(image: np.ndarray, readed_cards: List[ReadedCard], color=(0, 255, 0)) -> np.ndarray:
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