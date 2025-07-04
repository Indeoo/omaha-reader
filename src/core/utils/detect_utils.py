from typing import List

import numpy as np
from loguru import logger

from src.core.domain.captured_window import CapturedWindow
from src.core.domain.detection_result import GameSnapshot
from src.core.domain.readed_card import ReadedCard
from src.core.utils.opencv_utils import draw_detected_positions, save_opencv_image, draw_detected_bids, \
    draw_detected_cards


def save_detection_result_image(timestamp_folder: str, captured_image: CapturedWindow, game_snapshot: GameSnapshot):
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
                result_image = draw_cards(result_image, player_cards, color=(0, 255, 0))
                drawn_items.append(f"{len(player_cards)} player cards")

            if table_cards:
                result_image = draw_cards(result_image, table_cards,
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