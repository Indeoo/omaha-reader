from typing import List, Dict, Optional, Tuple

import numpy as np
import cv2

from src.domain.readed_card import ReadedCard
from src.omaha_card_reader import OmahaCardReader
from src.player_position_reader import PlayerPositionReader
from src.utils.opencv_utils import pil_to_cv2, save_opencv_image
from src.utils.template_matching_utils import draw_detected_cards


def detect_player_cards(cv2_image: np.ndarray, player_templates: Dict) -> List[ReadedCard]:
    """
    Detect player cards in the image

    Args:
        cv2_image: OpenCV format image
        player_templates: Dictionary of player card templates

    Returns:
        List of detected player cards
    """
    player_card_reader = OmahaCardReader(player_templates, OmahaCardReader.DEFAULT_SEARCH_REGION)
    return player_card_reader.read(cv2_image)


def detect_table_cards(cv2_image: np.ndarray, table_templates: Dict) -> List[ReadedCard]:
    """
    Detect table cards in the image

    Args:
        cv2_image: OpenCV format image
        table_templates: Dictionary of table card templates

    Returns:
        List of detected table cards
    """
    table_card_reader = OmahaCardReader(table_templates, None)
    return table_card_reader.read(cv2_image)


def detect_positions(cv2_image: np.ndarray, position_templates: Dict) -> List:
    """
    Detect player positions in the image

    Args:
        cv2_image: OpenCV format image
        position_templates: Dictionary of position templates

    Returns:
        List of detected positions
    """
    position_reader = PlayerPositionReader(position_templates)
    return position_reader.read(cv2_image)


def save_detection_result_image(timestamp_folder: str, captured_item: Dict, result: Dict):
    """
    Draw and save result image for a single captured image with detected cards and positions

    Args:
        timestamp_folder: Folder to save result images
        captured_item: Single captured image dictionary
        result: Processed result dictionary containing all detection info
    """
    window_name = captured_item['window_name']
    filename = captured_item['filename']

    try:
        cv2_image = pil_to_cv2(captured_item['image'])
        result_image = cv2_image.copy()

        # Track what we're drawing for debugging
        drawn_items = []

        # Draw cards if any detected
        if result['has_cards']:
            player_cards = result.get('player_cards', [])
            table_cards = result.get('table_cards', [])

            if player_cards:
                result_image = draw_cards(result_image, player_cards, color=(0, 255, 0))  # Green for player cards
                drawn_items.append(f"{len(player_cards)} player cards")

            if table_cards:
                result_image = draw_cards(result_image, table_cards,
                                          color=(0, 0, 255))  # Red for table cards (BGR format)
                drawn_items.append(f"{len(table_cards)} table cards")

        # Draw positions if any detected
        positions = result.get('positions', [])
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