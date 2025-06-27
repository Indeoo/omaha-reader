from typing import List, Dict, Union

import numpy as np
import cv2

from src.domain.readed_card import ReadedCard
from src.domain.detection_result import DetectionResult
from src.domain.captured_image import CapturedImage
from src.utils.opencv_utils import pil_to_cv2, save_opencv_image, draw_detected_cards


def save_detection_result_image(timestamp_folder: str, captured_image: CapturedImage, result: Union[Dict, DetectionResult]):
    """
    Draw and save result image for a single captured image with detected cards and positions

    Args:
        timestamp_folder: Folder to save result images
        captured_image: CapturedImage object
        result: DetectionResult object or dictionary containing all detection info
    """
    window_name = captured_image.window_name
    filename = captured_image.filename

    try:
        cv2_image = pil_to_cv2(captured_image.image)
        result_image = cv2_image.copy()

        # Track what we're drawing for debugging
        drawn_items = []

        # Handle both DetectionResult objects and dictionaries
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

        # Draw cards if any detected
        if has_cards:
            if player_cards:
                result_image = draw_cards(result_image, player_cards, color=(0, 255, 0))  # Green for player cards
                drawn_items.append(f"{len(player_cards)} player cards")

            if table_cards:
                result_image = draw_cards(result_image, table_cards,
                                          color=(0, 0, 255))  # Red for table cards (BGR format)
                drawn_items.append(f"{len(table_cards)} table cards")

        # Draw positions if any detected
        if positions:
            result_image = draw_detected_positions(result_image, positions)
            drawn_items.append(f"{len(positions)} positions")

        # Save result image
        result_filename = filename.replace('.png', '_result.png')
        save_opencv_image(result_image, timestamp_folder, result_filename)

        # Debug output
        if drawn_items:
            print(f"    📷 Saved {result_filename} with: {', '.join(drawn_items)}")
        else:
            print(f"    📷 Saved {result_filename} (no detections)")

    except Exception as e:
        print(f"    ❌ Error saving result image for {window_name}: {str(e)}")


def draw_detected_positions(image, positions):
    """
    Draw detected positions on the image

    Args:
        image: OpenCV image
        positions: List of DetectedPosition objects

    Returns:
        Image with drawn positions
    """
    result = image.copy()

    for pos in positions:
        x, y, w, h = pos.bounding_rect

        # Draw bounding rectangle in yellow
        cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 255), 2)

        # Draw center point in red
        cv2.circle(result, pos.center, 5, (0, 0, 255), -1)

        # Add label with position name and confidence
        label = f"{pos.position_name} ({pos.match_score:.2f})"
        cv2.putText(result, label, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    return result


def draw_cards(image: np.ndarray, readed_cards: List[ReadedCard], color=(0, 255, 0)) -> np.ndarray:
    """
    Draw detected cards on the image

    Args:
        image: Input image
        readed_cards: List of ReadedCard objects
        color: BGR color tuple for drawing cards

    Returns:
        Image with drawn detections
    """
    # Convert ReadedCard objects back to detection dictionaries
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

    # Use the extracted drawing function
    return draw_detected_cards(
        image=image,
        detections=detections,
        color=color,
        thickness=2,
        font_scale=0.6,
        show_scale=True
    )