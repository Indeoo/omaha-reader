from typing import List, Dict, Optional

import numpy as np
import cv2

from src.domain.readed_card import ReadedCard
from src.omaha_card_reader import OmahaCardReader
from src.player_position_reader import PlayerPositionReader
from src.utils.opencv_utils import pil_to_cv2, save_opencv_image
from src.utils.template_matching_utils import draw_detected_cards


def detect_cards_single(captured_item: Dict, image_index: int, player_templates: Dict, table_templates: Dict) -> \
Optional[Dict]:
    """
    Detect cards in a single captured image

    Args:
        captured_item: Single captured image dictionary
        image_index: Index of the image in the capture sequence
        player_templates: Dictionary of player card templates
        table_templates: Dictionary of table card templates

    Returns:
        Dictionary with detected card results, or None if no cards detected
    """
    player_card_reader = OmahaCardReader(player_templates, OmahaCardReader.DEFAULT_SEARCH_REGION)
    table_card_reader = OmahaCardReader(table_templates, None)

    window_name = captured_item['window_name']
    filename = captured_item['filename']

    try:
        cv2_image = pil_to_cv2(captured_item['image'])

        # Read cards
        player_cards = player_card_reader.read(cv2_image)
        table_cards = table_card_reader.read(cv2_image)

        # Return results if any cards detected
        if player_cards or table_cards:
            return {
                'window_name': window_name,
                'filename': filename,
                'image_index': image_index,
                'player_cards_raw': player_cards,
                'table_cards_raw': table_cards
            }
        return None

    except Exception as e:
        print(f"    ❌ Error processing {window_name}: {str(e)}")
        return None


def detect_positions_single(captured_item: Dict, image_index: int, position_templates: Dict) -> Dict:
    """
    Detect player positions in a single captured image

    Args:
        captured_item: Single captured image dictionary
        image_index: Index of the image in the capture sequence
        position_templates: Dictionary of position templates

    Returns:
        Dictionary with position results
    """
    position_reader = PlayerPositionReader(position_templates)

    window_name = captured_item['window_name']
    filename = captured_item['filename']

    try:
        cv2_image = pil_to_cv2(captured_item['image'])

        # Detect positions
        detected_positions = position_reader.read(cv2_image)

        return {
            'window_name': window_name,
            'filename': filename,
            'image_index': image_index,
            'positions': detected_positions
        }

    except Exception as e:
        print(f"    ❌ Error detecting positions in {window_name}: {str(e)}")
        return {
            'window_name': window_name,
            'filename': filename,
            'image_index': image_index,
            'positions': []
        }


def save_detection_result_image(timestamp_folder: str, captured_item: Dict,
                                card_result: Optional[Dict], position_result: Optional[Dict]):
    """
    Draw and save result image for a single captured image with detected cards and positions

    Args:
        timestamp_folder: Folder to save result images
        captured_item: Single captured image dictionary
        card_result: Detected card results for this image (can be None)
        position_result: Position results for this image (can be None)
    """
    window_name = captured_item['window_name']
    filename = captured_item['filename']

    try:
        cv2_image = pil_to_cv2(captured_item['image'])
        result_image = cv2_image.copy()

        # Track what we're drawing for debugging
        drawn_items = []

        # Draw cards if any detected
        if card_result:
            player_cards = card_result.get('player_cards_raw', [])
            table_cards = card_result.get('table_cards_raw', [])

            if player_cards:
                result_image = draw_cards(result_image, player_cards, color=(0, 255, 0))  # Green for player cards
                drawn_items.append(f"{len(player_cards)} player cards")

            if table_cards:
                result_image = draw_cards(result_image, table_cards,
                                          color=(0, 0, 255))  # Red for table cards (BGR format)
                drawn_items.append(f"{len(table_cards)} table cards")

        # Draw positions if any detected
        if position_result and position_result.get('positions'):
            positions = position_result['positions']
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