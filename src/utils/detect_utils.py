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