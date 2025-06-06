#!/usr/bin/env python3
"""
Simplified script that captures windows and analyzes them with PlayerCardReader.
Outputs enhanced format: WindowName: CardCardCard with Unicode suit symbols
"""
import ctypes
import os
import time
from datetime import datetime

import numpy as np
from typing import List

from src.capture.capture_utils import capture_windows, capture_and_save_windows
from src.cv.opencv_utils import pil_to_cv2
from src.deck.deck_utils import format_cards
from src.player_card_reader import PlayerCardReader
from src.readed_card import ReadedCard

# Try to enable DPI awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    ctypes.windll.user32.SetProcessDPIAware()


def analyze_image_for_cards(image: np.ndarray, player_card_reader: PlayerCardReader) -> List[ReadedCard]:
    """
    Analyze image and return just the card names found

    Args:
        image: OpenCV image (BGR format)
        player_card_reader: PlayerCardReader instance

    Returns:
        List of card names (e.g., ['9H', '8D', '5S', '4C'])
    """
    try:
        readed_cards = player_card_reader.read(image)
        # Sort cards by x-position (left to right) and extract template names
        sorted_cards = sorted(readed_cards, key=lambda card: card.center[0])
        return [card for card in sorted_cards]
    except Exception as e:
        print(f"    ❌ Error analyzing image: {str(e)}")
        return []


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

        print(f"📄 Detection results written to: {detection_file_path}")

    except Exception as e:
        print(f"❌ Error writing detection results: {str(e)}")


def main(capture_save=True):
    """
    Main function that captures windows and analyzes them for player cards
    """
    print("🚀 Starting Simplified Window Capture & Card Detection")
    print("=" * 60)

    # Configuration
    output_dir = "resources/simple_results"

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Capture windows
    print("\n📸 Capturing windows...")
    try:
        if capture_save:
            # Use convenience function that handles both capture and save with consistent timestamp
            session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            timestamp_folder, captured_images, windows = capture_and_save_windows(timestamp=session_timestamp)
            print(f"✅ Captured and saved {len(captured_images)} images")
        else:
            # Just capture without saving
            session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            captured_images, windows, _ = capture_windows(timestamp=session_timestamp)
            timestamp_folder = None
            print(f"✅ Captured {len(captured_images)} images")

        if not captured_images:
            print("❌ No images captured. Exiting.")
            return

    except Exception as e:
        print(f"❌ Error capturing windows: {str(e)}")
        return

    print(f"\n🔍 Analyzing {len(captured_images)} captured images...")

    # Analyze each captured image
    results = []
    total_hands = 0

    for i, captured_item in enumerate(captured_images, 1):
        filename = captured_item['filename']
        pil_image = captured_item['image']

        window_name = extract_window_name(filename)

        print(f"🔍 Analyzing {i}/{len(captured_images)}: {window_name}")

        try:
            # Convert PIL image to OpenCV format
            cv2_image = pil_to_cv2(pil_image)

            # Analyze with PlayerCardReader
            cards = analyze_image_for_cards(cv2_image, player_card_reader)

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
    print("\n🃏 DETECTED HANDS:")
    print("-" * 30)

    # First, form the data - collect all hands with cards
    detected_hands = []
    for result in results:
        if result['cards']:
            cards_unicode = format_cards(cards)
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

    # Write detection results to file if we have a timestamp folder
    if timestamp_folder and os.path.exists(timestamp_folder):
        write_detection_results(detected_hands, timestamp_folder)

    print("=" * 60)


def extract_window_name(filename: str) -> str:
    """
    Extract a clean window name from the filename

    Args:
        filename: Original filename like "01_PokerStars_exe_Lobby_Window.png"

    Returns:
        Clean window name like "PokerStars_Lobby"
    """
    # Remove file extension
    name = filename.replace('.png', '').replace('.jpg', '').replace('.jpeg', '')

    # Remove number prefix (e.g., "01_")
    if '_' in name:
        parts = name.split('_')
        if parts[0].isdigit() or parts[0].startswith('0'):
            name = '_'.join(parts[1:])

    # Simplify common patterns
    name = name.replace('_exe_', '_')
    name = name.replace('__', '_')

    # Limit length and clean up
    if len(name) > 30:
        name = name[:30]

    return name.strip('_')


if __name__ == "__main__":
    print("Player card reader")
    print("------------------------------")

    wait_time = 10

    # Initialize PlayerCardReader
    print("🎯 Initializing PlayerCardReader...")
    try:
        templates_dir = "resources/templates/player_cards/"
        player_card_reader = PlayerCardReader(templates_dir=templates_dir)

        if not player_card_reader.templates:
            raise Exception("❌ No templates loaded! Please check the templates directory.")

        print(f"✅ Loaded {len(player_card_reader.templates)} templates")

        try:
            while True:
                main()
                print(f"Sleep for {wait_time} second...")
                time.sleep(wait_time)
        except KeyboardInterrupt:
            print("\n🛑 Stopping capture loop...")
        except Exception as e:
            print(f"An error occurred: {e}")

    except Exception as e:
        print(f"❌ Error initializing PlayerCardReader: {str(e)}")