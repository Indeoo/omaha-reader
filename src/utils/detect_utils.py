from src.omaha_card_reader import OmahaCardReader
from src.utils.opencv_utils import pil_to_cv2, save_opencv_image


def detect_cards(timestamp_folder, captured_images, player_templates, table_templates):
    player_card_reader = OmahaCardReader(player_templates, OmahaCardReader.DEFAULT_SEARCH_REGION)
    table_card_reader = OmahaCardReader(table_templates, None)  # No search region for table cards

    detected_cards = []

    for captured_item in captured_images:
        window_name = captured_item['window_name']
        filename = captured_item['filename']

        try:
            cv2_image = pil_to_cv2(captured_item['image'])

            # Read cards
            player_cards = player_card_reader.read(cv2_image)
            table_cards = table_card_reader.read(cv2_image)

            # Save result image with detected cards
            result_image = player_card_reader.draw_detected_cards(cv2_image.copy(), player_cards)
            result_image = table_card_reader.draw_detected_cards(result_image, table_cards)
            save_opencv_image(result_image, timestamp_folder, filename.replace('.png', '_result.png'))

            # Add to results if any cards detected
            if player_cards or table_cards:
                detected_cards.append({
                    'window_name': window_name,
                    'player_cards_raw': player_cards,
                    'table_cards_raw': table_cards
                })

        except Exception as e:
            print(f"    ❌ Error processing {window_name}: {str(e)}")

    return detected_cards


def detect_positions(timestamp_folder, captured_images, position_templates):
    """
    Detect player positions in captured images

    Args:
        timestamp_folder: Folder to save results
        captured_images: List of captured image dictionaries
        position_templates: Dictionary of position templates

    Returns:
        List of position results
    """
    from src.player_position_reader import PlayerPositionReader

    position_reader = PlayerPositionReader(position_templates)
    position_results = []

    for captured_item in captured_images:
        window_name = captured_item['window_name']

        # Skip full screen capture for position detection
        if window_name == 'full_screen':
            continue

        try:
            cv2_image = pil_to_cv2(captured_item['image'])

            # Detect positions
            detected_positions = position_reader.read(cv2_image)

            position_results.append({
                'window_name': window_name,
                'positions': detected_positions
            })

            # Optional: Save result image with detected positions
            if detected_positions and timestamp_folder:
                result_image = draw_detected_positions(cv2_image.copy(), detected_positions)
                filename = captured_item['filename'].replace('.png', '_positions.png')
                save_opencv_image(result_image, timestamp_folder, filename)

        except Exception as e:
            print(f"    ❌ Error detecting positions in {window_name}: {str(e)}")
            position_results.append({
                'window_name': window_name,
                'positions': []
            })

    return position_results


def draw_detected_positions(image, positions):
    """
    Draw detected positions on the image

    Args:
        image: OpenCV image
        positions: List of DetectedPosition objects

    Returns:
        Image with drawn positions
    """
    import cv2

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