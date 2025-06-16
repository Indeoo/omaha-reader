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
from src.utils.result_utils import print_detection_result, print_position_result, write_combined_result

WAIT_TIME = 20


def process_captured_image():
    window_name = captured_item['window_name']
    filename = captured_item['filename']
    print(f"\n📷 Processing image {i + 1}/{len(captured_images)}: {window_name}")
    print("-" * 40)
    # Detect cards for single image
    card_result = detect_cards_single(captured_item, i, player_templates, table_templates)
    # Detect positions for single image (skip full screen)

    position_result = None
    if window_name != 'full_screen':
        position_result = detect_positions_single(captured_item, i, position_templates)
    # Write and print detection results for this image
    if card_result:
        print_detection_result(card_result)
    else:
        print(f"  🃏 No cards detected")
    # Write and print position results for this image
    if position_result:
        print_position_result(position_result)
    elif window_name != 'full_screen':
        print(f"  🎯 No positions detected")

    filename = f"detection_{filename}.txt"
    write_combined_result(card_result, position_result, timestamp_folder, filename)

    # Save result image with both cards and positions drawn
    save_detection_result_image(
        timestamp_folder,
        captured_item,
        card_result,
        position_result
    )


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

                print(f"\n🔄 Processing {len(captured_images)} captured images...")
                print("=" * 60)

                # Process each captured image individually
                for i, captured_item in enumerate(captured_images):
                    process_captured_image()

                print("\n" + "=" * 60)
                print(f"✅ Processing complete. Results saved to: {timestamp_folder}")
                print(f"\nSleep for {WAIT_TIME} seconds...")
                time.sleep(WAIT_TIME)
        except KeyboardInterrupt:
            print("\n🛑 Stopping capture loop...")
        except Exception as e:
            print(f"An error occurred: {e}")

    except Exception as e:
        print(f"❌ Error initializing readers: {str(e)}")
