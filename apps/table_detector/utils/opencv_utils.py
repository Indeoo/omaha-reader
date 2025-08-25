import os
from typing import List, Dict, Tuple

import cv2
import numpy as np
from PIL import Image
from loguru import logger

from shared.domain.detected_bid import DetectedBid


def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
    if pil_image.mode in ('RGBA', 'LA'):
        logger.info(f"Warning: Alpha channel in {pil_image.mode} image will be removed")

    if pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')

    cv2_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    return cv2_image


def save_opencv_image(image, folder_path, filename):
    os.makedirs(folder_path, exist_ok=True)
    filepath = os.path.join(folder_path, filename)
    cv2.imwrite(filepath, image)


def match_cv2_template(scaled_h, scaled_w, search_image, template):
    scaled_template = cv2.resize(template, (scaled_w, scaled_h))
    result = cv2.matchTemplate(search_image, scaled_template, cv2.TM_CCORR_NORMED)
    return result


def read_cv2_image(tpl_path):
    return cv2.imread(tpl_path, cv2.IMREAD_COLOR)


def draw_detected_bids(
        image: np.ndarray,
        detected_bids: Dict[int, DetectedBid],
        color: Tuple[int, int, int] = (255, 0, 255),  # Magenta for bids
        thickness: int = 2,
        font_scale: float = 0.6
) -> np.ndarray:
    result = image.copy()

    for bid in detected_bids.values():
        label = f"P{bid.position}: ${bid.amount_text}"
        x, y, w, h = bid.bounding_rect

        cv2.rectangle(result, (x, y), (x + w, y + h), color, thickness)
        cv2.putText(result, label, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)

    return result


def coords_to_search_region(x: int, y: int, w: int, h: int,
                            image_width= 784, image_height = 584) -> tuple[float, float, float, float]:
    left = x / image_width
    top = y / image_height
    right = (x + w) / image_width
    bottom = (y + h) / image_height

    left = max(0.0, min(1.0, left))
    top = max(0.0, min(1.0, top))
    right = max(0.0, min(1.0, right))
    bottom = max(0.0, min(1.0, bottom))

    return (left, top, right, bottom)


def match_template_at_scale(
        search_image: np.ndarray,
        template: np.ndarray,
        template_name: str,
        scale: float,
        template_w: int,
        template_h: int,
        offset: Tuple[int, int],
        match_threshold: float = 0.955,
        min_card_size: int = 5
) -> List[Dict]:
    """
    Perform template matching at a specific scale

    Args:
        search_image: Image region to search in
        template: Template image
        template_name: Name of the template
        scale: Scale factor
        template_w: Template width
        template_h: Template height
        offset: (x, y) offset of search region
        match_threshold: Minimum match score to consider
        min_card_size: Minimum card size in pixels

    Returns:
        List of detection dictionaries
    """
    scaled_w = int(template_w * scale)
    scaled_h = int(template_h * scale)

    # # Skip if template becomes too small or too large
    # if (scaled_w < min_card_size or scaled_h < min_card_size or
    #         scaled_w > search_image.shape[1] or scaled_h > search_image.shape[0]):
    #     return []

    # Resize template
    scaled_template = cv2.resize(template, (scaled_w, scaled_h))

    # Perform template matching
    result = cv2.matchTemplate(search_image, scaled_template, cv2.TM_CCORR_NORMED)

    # Find all locations where match is above threshold
    locations = np.where(result >= match_threshold)
    detections = []

    for y, x in zip(*locations):
        match_score = result[y, x]
        center_x = x + scaled_w // 2
        center_y = y + scaled_h // 2

        detection = {
            'template_name': template_name,
            'match_score': float(match_score),
            'bounding_rect': (x + offset[0], y + offset[1], scaled_w, scaled_h),
            'center': (center_x + offset[0], center_y + offset[1]),
            'scale': scale,
            'template_size': (template_w, template_h),
            'scaled_size': (scaled_w, scaled_h)
        }
        detections.append(detection)

    return detections