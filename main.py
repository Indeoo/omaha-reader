#!/usr/bin/env python3
"""
Simplified script that captures windows and analyzes them with PlayerCardReader.
Outputs enhanced format: WindowName: CardCardCard with Unicode suit symbols
"""
import os
import time
from datetime import datetime

from src.utils.capture_utils import capture_and_save_windows
from src.utils.detect_utils import detect_cards
from src.utils.opencv_utils import load_templates
from src.utils.result_utils import write_detection_results, print_detection_results


WAIT_TIME = 20

if __name__ == "__main__":
    print("🎯 Initializing Omaha Card Reader")
    print("------------------------------")

    try:
        player_templates = load_templates("resources/templates/player_cards/")
        table_templates = load_templates("resources/templates/table_cards/")
        working_dir = os.getcwd()

        try:
            while True:
                session_timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
                timestamp_folder = os.path.join(working_dir, f"Dropbox/data_screenshots/{session_timestamp}")
                os.makedirs(timestamp_folder, exist_ok=True)
                captured_images = capture_and_save_windows(timestamp_folder=timestamp_folder, save_windows=True)

                # Single unified call to detect_cards with both template sets
                detected_hands = detect_cards(timestamp_folder, captured_images, player_templates, table_templates)

                # Write and print results using the unified detected_hands
                write_detection_results(detected_hands, timestamp_folder)
                print_detection_results(detected_hands)

                print(f"Sleep for {WAIT_TIME} second...")
                time.sleep(WAIT_TIME)
        except KeyboardInterrupt:
            print("\n🛑 Stopping capture loop...")
        except Exception as e:
            print(f"An error occurred: {e}")

    except Exception as e:
        print(f"❌ Error initializing PlayerCardReader: {str(e)}")