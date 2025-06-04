#!/usr/bin/env python3
"""
Simplified script that captures windows and analyzes them with PlayerCardReader.
Outputs enhanced format: WindowName: CardCardCard with Unicode suit symbols
"""
import ctypes
import os
import time

import numpy as np
from typing import List

from src.capture.capture_utils import capture_windows, save_windows
from src.cv.opencv_utils import pil_to_cv2
from src.deck.deck_utils import format_cards_with_unicode
from src.player_card_reader import PlayerCardReader

# Try to enable DPI awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    ctypes.windll.user32.SetProcessDPIAware()


def analyze_image_for_cards(image: np.ndarray, player_card_reader: PlayerCardReader) -> List[str]:
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
        return [card.template_name for card in sorted_cards]
    except Exception as e:
        print(f"    ❌ Error analyzing image: {str(e)}")
        return []


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
        captured_images, windows = capture_windows()
        print(f"✅ Captured {len(captured_images)} images")

        if not captured_images:
            print("❌ No images captured. Exiting.")
            return

    except Exception as e:
        print(f"❌ Error capturing windows: {str(e)}")
        return

    if capture_save:
        save_windows(captured_images, windows)

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
                cards_unicode = format_cards_with_unicode(cards)
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
            cards_unicode = format_cards_with_unicode(result['cards'])
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

    print("=" * 60)


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