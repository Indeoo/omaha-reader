#!/usr/bin/env python3
"""
Simplified script that captures windows and analyzes them with PlayerCardReader.
Outputs enhanced format: WindowName: CardCardCard with Unicode suit symbols
"""
import os
import time
from datetime import datetime

from src.utils.capture_utils import capture_and_save_windows
from src.utils.opencv_utils import load_templates
from src.utils.shared_processing import process_captured_images, format_results_for_console

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

                print(f"\n🔄 Processing {len(captured_images)} captured images...")
                print("=" * 60)

                # Process all captured images using shared function
                processed_results = process_captured_images(
                    captured_images=captured_images,
                    player_templates=player_templates,
                    table_templates=table_templates,
                    position_templates=position_templates,
                    detect_positions=True
                )

                # Format and output results for console
                format_results_for_console(
                    processed_results=processed_results,
                    timestamp_folder=timestamp_folder,
                    save_result_images=True,
                    write_result_files=True
                )

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