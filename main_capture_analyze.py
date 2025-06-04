#!/usr/bin/env python3
"""
Simplified script that captures windows and analyzes them with PlayerCardReader.
Outputs simple format: WindowName: CardCardCard
"""

import os
import time

import cv2
import numpy as np
from datetime import datetime
from typing import List, Dict, Any
from PIL import Image

from src.capture.capture_utils import capture_windows
from src.cv.opencv_utils import pil_to_cv2
from src.player_card_reader import PlayerCardReader
from src.readed_card import ReadedCard


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


# def write_simplified_results(results: List[Dict[str, Any]], output_path: str) -> None:
#     """
#     Write simplified results to file
#
#     Args:
#         results: List of analysis results
#         output_path: Path to output file
#     """
#     try:
#         with open(output_path, 'w', encoding='utf-8') as f:
#             f.write(f"Player Hand Detection Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
#             f.write("=" * 60 + "\n\n")
#
#             hands_found = 0
#
#             for result in results:
#                 window_name = result['window_name']
#                 cards = result['cards']
#
#                 if cards:
#                     cards_str = ''.join(cards)
#                     f.write(f"{window_name}: {cards_str}\n")
#                     hands_found += 1
#                 else:
#                     f.write(f"{window_name}: No cards detected\n")
#
#             f.write(f"\nTotal windows with hands detected: {hands_found}/{len(results)}\n")
#
#     except Exception as e:
#         print(f"❌ Error writing results file: {str(e)}")
#         raise


def main():
    """
    Main function that captures windows and analyzes them for player cards
    """
    print("🚀 Starting Simplified Window Capture & Card Detection")
    print("=" * 60)

    # Configuration
    templates_dir = "resources/templates/player_cards/"
    output_dir = "resources/simple_results"

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Initialize PlayerCardReader
    print("🎯 Initializing PlayerCardReader...")
    try:
        player_card_reader = PlayerCardReader(templates_dir=templates_dir)

        if not player_card_reader.templates:
            print("❌ No templates loaded! Please check the templates directory.")
            return

        print(f"✅ Loaded {len(player_card_reader.templates)} templates")

    except Exception as e:
        print(f"❌ Error initializing PlayerCardReader: {str(e)}")
        return

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

    # Create timestamped output file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"hands_{timestamp}.txt"
    output_path = os.path.join(output_dir, output_filename)

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

            # Print immediate result
            if cards:
                cards_str = ''.join(cards)
                print(f"    ✅ {window_name}: {cards_str}")
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

    # # Write results to file
    # print(f"\n💾 Writing results to {output_filename}...")
    # try:
    #     write_simplified_results(results, output_path)
    #     print(f"✅ Results saved to: {output_path}")
    #
    # except Exception as e:
    #     print(f"❌ Error writing results: {str(e)}")
    #     return
    #
    # # Print final summary
    # print("\n" + "=" * 60)
    # print("🎉 DETECTION COMPLETE!")
    # print("=" * 60)
    # print(f"Windows analyzed: {len(captured_images)}")
    # print(f"Hands detected: {total_hands}")
    # print(f"📄 Results saved to: {output_path}")

    # Also print results to console for immediate viewing
    print("\n🃏 DETECTED HANDS:")
    print("-" * 30)
    hands_shown = 0
    for result in results:
        if result['cards']:
            cards_str = ''.join(result['cards'])
            print(f"{result['window_name']}: {cards_str}")
            hands_shown += 1

    if hands_shown == 0:
        print("No hands detected in any window.")

    print("=" * 60)


if __name__ == "__main__":
    print("Player card reader")
    print("------------------------------")

    try:
        while True:
            main()
            print("Sleep for 3 second...")
            time.sleep(3)
    except Exception as e:
        print(f"An error occurred: {e}")
