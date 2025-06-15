#!/usr/bin/env python3
"""
Simplified script that captures windows and analyzes them with PlayerCardReader.
Outputs enhanced format: WindowName: CardCardCard with Unicode suit symbols
"""
import ctypes
import os
import time
from datetime import datetime

from typing import List

from src.capture.capture_utils import capture_and_save_windows
from src.cv.opencv_utils import pil_to_cv2, save_opencv_image
from src.deck.deck_utils import format_cards
from src.player_card_reader import PlayerCardReader
from src.utils.template_loader import load_templates

# Try to enable DPI awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    ctypes.windll.user32.SetProcessDPIAware()


def write_detection_results(detected_hands: List[dict], timestamp_folder: str):
    """
    Write detection results to detection.txt in the timestamp folder

    Args:
        detected_hands: List of detected hands with window names and cards
        timestamp_folder: Path to the timestamp folder where detection.txt should be saved
    """
    detection_file_path = os.path.join(timestamp_folder, "detection.txt")

    try:
        with open(detection_file_path, 'w', encoding='utf-8') as f:
            f.write(f"Card Detection Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")

            if detected_hands:
                f.write(f"🃏 DETECTED HANDS ({len(detected_hands)} total):\n")
                f.write("-" * 30 + "\n")

                for hand in detected_hands:
                    f.write(f"{hand['window_name']}: {hand['cards_unicode']}\n")
            else:
                f.write("No hands detected in any window.\n")

            f.write("\n" + "=" * 60 + "\n")

        #print(f"📄 Detection results written to: {detection_file_path}")

    except Exception as e:
        print(f"❌ Error writing detection results: {str(e)}")


def detect_cards(timestamp_folder, captured_images, templates):
    """
    Main function that captures windows and analyzes them for player cards
    """
    print("🚀 Starting Card Detection")
    print("=" * 60)

    player_card_reader = PlayerCardReader(templates)

    #print(f"\n🔍 Analyzing {len(captured_images)} captured images...")

    # Analyze each captured image
    results = []
    total_hands = 0

    for i, captured_item in enumerate(captured_images, 1):
        filename = captured_item['filename']
        pil_image = captured_item['image']
        window_name = captured_item['window_name']
        result_image_name =  filename.replace('.png', '_result.png')
        #window_name = extract_window_name(filename)

        #print(f"🔍 Analyzing {i}/{len(captured_images)}: {window_name}")

        try:
            # Convert PIL image to OpenCV format
            cv2_image = pil_to_cv2(pil_image)

            # Analyze with PlayerCardReader
            cards = player_card_reader.read(cv2_image)

            #cards = analyze_image_for_cards(cv2_image, player_card_reader)

            result_image = player_card_reader.draw_detected_cards(cv2_image, cards)
            save_opencv_image(result_image, timestamp_folder, result_image_name)

            result = {
                'window_name': window_name,
                'cards': cards,
                'original_filename': filename
            }
            results.append(result)

            # Print immediate result with Unicode symbols
            if cards:
                cards_unicode = format_cards(cards)
                print(f"    ✅ {window_name}: {cards_unicode}")
                total_hands += 1
            else:
                print(f"    ⚪ {window_name}: No cards detected")

        except Exception as e:
            print(f"    ❌ Error processing {window_name}: {str(e)}")
            result = {
                'window_name': window_name,
                'cards': [],
                'original_filename': filename
            }
            results.append(result)

    # Also print results to console for immediate viewing
    #print("\n🃏 DETECTED HANDS:")
    print("-" * 30)

    # First, form the data - collect all hands with cards
    detected_hands = []
    for result in results:
        if result['cards']:
            cards_unicode = format_cards(result['cards'])  # Fixed: use result['cards'] instead of cards
            detected_hands.append({
                'window_name': result['window_name'],
                'cards_unicode': cards_unicode,
                'cards_raw': result['cards']
            })

    # Then, view the data in a separate loop
    hands_shown = 0
    for hand in detected_hands:
        print(f"{hand['window_name']}: {hand['cards_unicode']}")
        hands_shown += 1

    if hands_shown == 0:
        print("No hands detected in any window.")

    return detected_hands
    # # Write detection results to file if we have a timestamp folder
    # if timestamp_folder and os.path.exists(timestamp_folder):
    #     write_detection_results(detected_hands, timestamp_folder)
    #
    # print("=" * 60)


def capture_images(timestamp_folder, capture_save=True):
    # Capture windows
    print("\n📸 Capturing windows...")
    try:
        if capture_save:
            # Use convenience function that handles both capture and save with consistent timestamp
            captured_images, windows = capture_and_save_windows(timestamp_folder=timestamp_folder)
            print(f"✅ Captured and saved {len(captured_images)} images")
        else:
            # Just capture without saving
            captured_images, windows = capture_and_save_windows(timestamp_folder=timestamp_folder)
            print(f"✅ Captured {len(captured_images)} images")

        if not captured_images:
            raise Exception("❌ No images captured. Exiting.")

    except Exception as e:
        raise Exception(f"❌ Error capturing windows: {str(e)}")
    return captured_images


if __name__ == "__main__":
    print("Omaha Card Reader")
    print("------------------------------")

    WAIT_TIME = 20

    # Initialize PlayerCardReader
    print("🎯 Initializing Card Reader...")
    try:
        player_templates = load_templates("resources/templates/player_cards/")
        table_templates = load_templates("resources/templates/table_cards/")

        if not player_templates:
            raise Exception("❌ No player templates loaded! Please check the templates directory.")
        if not table_templates:
            raise Exception("❌ No table templates loaded! Please check the templates directory.")

        print(f"✅ Loaded {len(player_templates)} player card templates")
        print(f"✅ Loaded {len(table_templates)} table card templates")

        try:
            while True:
                session_timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
                # Create timestamped output folder using provided timestamp
                working_dir = os.getcwd()
                timestamp_folder = os.path.join(working_dir, f"Dropbox/data_screenshots/{session_timestamp}")
                os.makedirs(timestamp_folder, exist_ok=True)
                captured_images = capture_images(timestamp_folder)

                detected_hands = detect_cards(timestamp_folder, captured_images, player_templates)
                if timestamp_folder and os.path.exists(timestamp_folder):
                    write_detection_results(detected_hands, timestamp_folder)

                detected_table = detect_cards(timestamp_folder, captured_images, table_templates)
                if timestamp_folder and os.path.exists(timestamp_folder):
                    write_detection_results(detected_table, timestamp_folder)

                print(f"Sleep for {WAIT_TIME} second...")
                time.sleep(WAIT_TIME)
        except KeyboardInterrupt:
            print("\n🛑 Stopping capture loop...")
        except Exception as e:
            print(f"An error occurred: {e}")

    except Exception as e:
        print(f"❌ Error initializing PlayerCardReader: {str(e)}")