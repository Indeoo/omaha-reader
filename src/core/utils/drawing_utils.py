import traceback
from typing import List, Dict, Tuple
import cv2
import numpy as np
from loguru import logger

from src.core.domain.captured_window import CapturedWindow
from src.core.domain.detected_bid import DetectedBid
from src.core.domain.game_snapshot import GameSnapshot
from src.core.domain.detection import Detection
from src.core.utils.opencv_utils import save_opencv_image


def save_detection_result(timestamp_folder: str, captured_image: CapturedWindow, game_snapshot: GameSnapshot):
    window_name = captured_image.window_name
    filename = captured_image.filename

    try:
        cv2_image = captured_image.get_cv2_image()
        result_image = cv2_image.copy()

        drawn_items = []

        player_cards = game_snapshot.player_cards
        table_cards = game_snapshot.table_cards
        positions = game_snapshot.positions
        bids = game_snapshot.bids
        actions = game_snapshot.actions

        result_image = draw_detected_cards(result_image, player_cards, color=(0, 255, 0))
        drawn_items.append(f"{len(player_cards)} player cards")

        result_image = draw_detected_cards(result_image, table_cards, color=(0, 0, 255))
        drawn_items.append(f"{len(table_cards)} table cards")

        result_image = draw_detected_positions(result_image, list(positions.values()))
        drawn_items.append(f"{len(positions)} positions")

        converted_bids_detections = _convert_bids_to_detections(bids)
        result_image = draw_detected_bids(result_image, converted_bids_detections)
        drawn_items.append(f"{len(bids)} bids")

        converted_detections = _flatten_action_lists(actions)
        result_image = draw_detected_actions(result_image, converted_detections)
        drawn_items.append(f"{len(actions)} actions")

        result_filename = filename.replace('.png', '_result.png')
        save_opencv_image(result_image, timestamp_folder, result_filename)

        if drawn_items:
            logger.info(f"    📷 Saved {result_filename} with: {', '.join(drawn_items)}")
        else:
            logger.info(f"    📷 Saved {result_filename} (no detections)")

    except Exception as e:
        logger.error(f"    ❌ Error saving result image for {window_name}: {str(e)}")
        raise e


def _draw_detections(
        image: np.ndarray,
        detections: List[Detection],
        color: Tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2,
        font_scale: float = 0.6
) -> np.ndarray:
    result = image.copy()

    for detection in detections:
        x, y, w, h = detection.bounding_rect
        cv2.rectangle(result, (x, y), (x + w, y + h), color, thickness)
        cv2.circle(result, detection.center, 5, (255, 0, 0), -1)
        cv2.putText(result, f"{detection.name} ({detection.match_score:.2f})", (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)

    return result


def _convert_bids_to_detections(detected_bids: Dict[int, DetectedBid]) -> List[Detection]:
    detections = []

    for bid in detected_bids.values():
        detection = Detection(
            name=f"P{bid.position}: ${bid.amount_text}",
            center=bid.center,
            bounding_rect=bid.bounding_rect,
            match_score=1.0
        )
        detections.append(detection)
    return detections


def _flatten_action_lists(user_actions: Dict[int, List[Detection]]) -> List[Detection]:
    detections = []
    for action_list in user_actions.values():
        detections.extend(action_list)
    return detections

def draw_detected_cards(image: np.ndarray, detections: List[Detection], color=(0, 255, 0),
                        thickness=2, font_scale=0.6, show_scale=True) -> np.ndarray:
    try:
        result = _draw_detections(image, detections, color, thickness, font_scale)

        if show_scale and detections:
            for detection in detections:
                if hasattr(detection, 'scale'):
                    x, y, w, h = detection.bounding_rect
                    cv2.putText(result, f"Scale: {detection.scale:.1f}", (x, y + h + 20),
                                cv2.FONT_HERSHEY_SIMPLEX, font_scale * 0.7, (255, 255, 0), 1)
        return result
    except Exception as e:
        logger.error("Error drawing cards: ", e)
        raise e


def draw_detected_positions(image: np.ndarray, detections: List[Detection]) -> np.ndarray:
    return _draw_detections(image, detections, color=(0, 255, 255))


def draw_detected_bids(image: np.ndarray, detections: List[Detection], color=(255, 0, 255),
                       thickness=2, font_scale=0.6) -> np.ndarray:
    return _draw_detections(image, detections, color, thickness, font_scale)


def draw_detected_actions(image: np.ndarray, detections: List[Detection]) -> np.ndarray:
    return _draw_detections(image, detections, color=(0, 255, 255))
