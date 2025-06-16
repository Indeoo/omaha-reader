from typing import List

import numpy as np
import cv2

from src.domain.readed_card import ReadedCard
from src.omaha_card_reader import OmahaCardReader
from src.utils.opencv_utils import pil_to_cv2, save_opencv_image
from src.utils.template_matching_utils import draw_detected_cards


def detect_cards(captured_images, player_templates, table_templates):
    """
    Detect cards in captured images and return results only

    Args:
        timestamp_folder: Folder path (not used in this function anymore)
        captured_images: List of captured image dictionaries
        player_templates: Dictionary of player card templates
        table_templates: Dictionary of table card templates

    Returns:
        List of detected card results
    """
    player_card_reader = OmahaCardReader(player_templates, OmahaCardReader.DEFAULT_SEARCH_REGION)
    table_card_reader = OmahaCardReader(table_templates, None)  # No search region for table cards

    detected_cards = []

    for i, captured_item in enumerate(captured_images):
        window_name = captured_item['window_name']
        filename = captured_item['filename']

        try:
            cv2_image = pil_to_cv2(captured_item['image'])

            # Read cards
            player_cards = player_card_reader.read(cv2_image)
            table_cards = table_card_reader.read(cv2_image)

            # Add to results if any cards detected - use index and filename for unique identification
            if player_cards or table_cards:
                detected_cards.append({
                    'window_name': window_name,
                    'filename': filename,  # Add filename for unique matching
                    'image_index': i,  # Add index for unique matching
                    'player_cards_raw': player_cards,
                    'table_cards_raw': table_cards
                })

        except Exception as e:
            print(f"    ❌ Error processing {window_name}: {str(e)}")

    return detected_cards


def detect_positions(captured_images, position_templates):
    """
    Detect player positions in captured images and return results only

    Args:
        timestamp_folder: Folder path (not used in this function anymore)
        captured_images: List of captured image dictionaries
        position_templates: Dictionary of position templates

    Returns:
        List of position results
    """
    from src.player_position_reader import PlayerPositionReader

    position_reader = PlayerPositionReader(position_templates)
    position_results = []

    for i, captured_item in enumerate(captured_images):
        window_name = captured_item['window_name']
        filename = captured_item['filename']

        # Skip full screen capture for position detection
        if window_name == 'full_screen':
            continue

        try:
            cv2_image = pil_to_cv2(captured_item['image'])

            # Detect positions
            detected_positions = position_reader.read(cv2_image)

            position_results.append({
                'window_name': window_name,
                'filename': filename,  # Add filename for unique matching
                'image_index': i,  # Add index for unique matching
                'positions': detected_positions
            })

        except Exception as e:
            print(f"    ❌ Error detecting positions in {window_name}: {str(e)}")
            position_results.append({
                'window_name': window_name,
                'filename': filename,
                'image_index': i,
                'positions': []
            })

    return position_results


def save_detection_results_images(timestamp_folder, captured_images, detected_cards, position_results):
    """
    Draw and save result images with both detected cards and positions

    Args:
        timestamp_folder: Folder to save result images
        captured_images: List of captured image dictionaries
        detected_cards: List of detected card results
        position_results: List of position results
    """
    # Create lookup dictionaries using filename for unique identification
    cards_lookup = {item['filename']: item for item in detected_cards}
    positions_lookup = {item['filename']: item for item in position_results}

    for captured_item in captured_images:
        window_name = captured_item['window_name']
        filename = captured_item['filename']

        try:
            cv2_image = pil_to_cv2(captured_item['image'])
            result_image = cv2_image.copy()

            # Track what we're drawing for debugging
            drawn_items = []

            # Draw cards if any detected for this specific file
            if filename in cards_lookup:
                card_data = cards_lookup[filename]
                player_cards = card_data.get('player_cards_raw', [])
                table_cards = card_data.get('table_cards_raw', [])

                if player_cards:
                    result_image = draw_cards(result_image, player_cards, color=(0, 255, 0))  # Green for player cards
                    drawn_items.append(f"{len(player_cards)} player cards")

                if table_cards:
                    result_image = draw_cards(result_image, table_cards,
                                              color=(0, 0, 255))  # Red for table cards (BGR format)
                    drawn_items.append(f"{len(table_cards)} table cards")

            # Draw positions if any detected for this specific file
            if filename in positions_lookup:
                position_data = positions_lookup[filename]
                positions = position_data.get('positions', [])

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