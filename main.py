#!/usr/bin/env python3
"""
Simplified script that captures windows and analyzes them with PlayerCardReader.
Outputs enhanced format: WindowName: CardCardCard with Unicode suit symbols
"""
import os
import time
from datetime import datetime

from src.utils.capture_utils import capture_and_save_windows
from src.utils.detect_utils import detect_cards_single, detect_positions_single, save_detection_result_image
from src.utils.opencv_utils import load_templates
from src.utils.result_utils import write_detection_results, print_detection_results, write_position_results, \
    print_position_results

WAIT_TIME = 20

if __name__ == "__main__":
    print("🎯 Initializing Omaha Card Reader")
    print("------------------------------")

    try:
        player_templates = load_templates("resources/templates/player_cards/")
        table_templates = load_templates("resources/templates/table_cards/")
        position_templates = load_templates("resources/templates/positions/")
        working_dir = os.getcwd()

        try:
            while True:
                session_timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
                # timestamp_folder = os.path.join(working_dir, f"Dropbox/data_screenshots/{session_timestamp}")
                timestamp_folder = os.path.join(working_dir, f"_20250610_023049/_20250610_025342")

                os.makedirs(timestamp_folder, exist_ok=True)
                captured_images = capture_and_save_windows(timestamp_folder=timestamp_folder, save_windows=False,
                                                           debug=True)

                # Process each captured image individually
                detected_hands = []
                position_results = []

                for i, captured_item in enumerate(captured_images):
                    # Detect cards for single image
                    card_result = detect_cards_single(captured_item, i, player_templates, table_templates)
                    if card_result:  # Only add if cards were detected
                        detected_hands.append(card_result)

                    # Detect positions for single image (skip full screen)
                    if captured_item['window_name'] != 'full_screen':
                        position_result = detect_positions_single(captured_item, i, position_templates)
                        position_results.append(position_result)

                    # Save result image with both cards and positions drawn
                    # Find matching results for this specific image
                    matching_card_result = next((h for h in detected_hands if h['image_index'] == i), None)
                    matching_position_result = next((p for p in position_results if p['image_index'] == i), None)

                    save_detection_result_image(
                        timestamp_folder,
                        captured_item,
                        matching_card_result,
                        matching_position_result
                    )

                # Write and print card results
                write_detection_results(detected_hands, timestamp_folder)
                print_detection_results(detected_hands)

                # Write and print position results
                write_position_results(position_results, timestamp_folder)
                print_position_results(position_results)

                print(f"\nSleep for {WAIT_TIME} seconds...")
                time.sleep(WAIT_TIME)
        except KeyboardInterrupt:
            print("\n🛑 Stopping capture loop...")
        except Exception as e:
            print(f"An error occurred: {e}")

    except Exception as e:
        print(f"❌ Error initializing readers: {str(e)}")