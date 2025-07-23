from typing import List, Dict, Tuple, Union
import cv2
import numpy as np
from loguru import logger

from src.core.domain.detected_bid import DetectedBid
from src.core.service.template_matcher_service import Detection


def _draw_detections(
        image: np.ndarray,
        detections: Union[List[Detection], Dict[int, DetectedBid], List[List[Detection]]],
        color: Tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2,
        font_scale: float = 0.6
) -> np.ndarray:
    result = image.copy()

    # Handle different input types
    items_to_draw = []

    if isinstance(detections, dict):
        # Dict[int, DetectedBid]
        for bid in detections.values():
            items_to_draw.append({
                'rect': bid.bounding_rect,
                'center': bid.center,
                'label': f"P{bid.position}: ${bid.amount_text}"
            })
    elif isinstance(detections, list) and detections and isinstance(detections[0], list):
        # List[List[Detection]] - flatten
        for action_list in detections:
            for action in action_list:
                items_to_draw.append({
                    'rect': action.bounding_rect,
                    'center': action.center,
                    'label': f"{action.name} ({action.match_score:.2f})"
                })
    else:
        # List[Detection]
        for detection in detections:
            items_to_draw.append({
                'rect': detection.bounding_rect,
                'center': detection.center,
                'label': f"{detection.name} ({detection.match_score:.2f})"
            })

    # Draw all items
    for item in items_to_draw:
        x, y, w, h = item['rect']
        cv2.rectangle(result, (x, y), (x + w, y + h), color, thickness)
        cv2.circle(result, item['center'], 5, (255, 0, 0), -1)
        cv2.putText(result, item['label'], (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)

    return result


def draw_detected_cards(image, detections, color=(0, 255, 0), thickness=2, font_scale=0.6, show_scale=True):
    try:
        result = _draw_detections(image, detections, color, thickness, font_scale)

        if show_scale and detections:
            # Add scale info for cards
            for detection in detections:
                if hasattr(detection, 'scale'):
                    x, y, w, h = detection.bounding_rect
                    cv2.putText(result, f"Scale: {detection.scale:.1f}", (x, y + h + 20),
                                cv2.FONT_HERSHEY_SIMPLEX, font_scale * 0.7, (255, 255, 0), 1)
        return result
    except Exception as e:
        logger.error("Error drawing cards: ", e)
        raise e


def draw_detected_positions(image, positions):
    return _draw_detections(image, positions, color=(0, 255, 255))


def draw_detected_bids(image, detected_bids, color=(255, 0, 255), thickness=2, font_scale=0.6):
    return _draw_detections(image, detected_bids, color, thickness, font_scale)


def draw_detected_actions(image, user_actions):
    return _draw_detections(image, user_actions, color=(0, 255, 255))