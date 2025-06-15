#!/usr/bin/env python3
"""
Simplified script that captures windows and analyzes them with PlayerCardReader.
Outputs enhanced format: WindowName: CardCardCard with Unicode suit symbols
"""
import os
import time
from datetime import datetime

from typing import List

from src.utils.capture_utils import capture_and_save_windows
from src.utils.opencv_utils import pil_to_cv2, save_opencv_image, load_templates
from src.utils.deck_utils import format_cards
from src.player_card_reader import OmahaCardReader


def write_detection_results(detected_hands: List[dict], timestamp_folder: str):
    """
    Write detection results to detection.txt in the timestamp folder

    Args:
        detected_hands: List of detected hands with window names and both player/table cards
        timestamp_folder: Path to the timestamp folder where detection.txt should be saved
    """
    detection_file_path = os.path.join(timestamp_folder, "detection.txt")

    try:
        with open(detection_file_path, 'w', encoding='utf-8') as f:
            f.write(f"Card Detection Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")

            if detected_hands:
                f.write(f"🃏 DETECTED CARDS ({len(detected_hands)} windows):\n")
                f.write("-" * 30 + "\n")

                for hand in detected_hands:
                    window_name = hand['window_name']

                    # Combine player and table cards in one line
                    combined_cards = ""
                    if hand['player_cards_unicode']:
                        combined_cards += f"Player:{hand['player_cards_unicode']}"
                    if hand['table_cards_unicode']:
                        if combined_cards:
                            combined_cards += f" Table:{hand['table_cards_unicode']}"
                        else:
                            combined_cards += f"Table:{hand['table_cards_unicode']}"

                    if combined_cards:
                        f.write(f"{window_name}: {combined_cards}\n")
                    else:
                        f.write(f"{window_name}: No cards detected\n")
            else:
                f.write("No cards detected in any window.\n")

            f.write("\n" + "=" * 60 + "\n")

    except Exception as e:
        print(f"❌ Error writing detection results: {str(e)}")


def print_detection_results(detected_hands: List[dict]):
    """
    Print detection results to console with colored cards based on suit

    Args:
        detected_hands: List of detected hands with window names and both player/table cards
    """

    def colorize_cards(cards_string):
        """Apply color to cards based on suit"""
        if not cards_string:
            return cards_string

        # ANSI color codes - using brighter colors for better visibility on Windows
        colors = {
            'D': '\033[94m',  # Bright Blue for Diamonds
            'H': '\033[91m',  # Bright Red for Hearts
            'C': '\033[92m',  # Bright Green for Clubs
            'S': '\033[90m',  # Bright Black (Dark Gray) for Spades
        }
        reset = '\033[0m'

        import re
        # Find all card patterns (1-2 digits/letters followed by a suit)
        card_pattern = r'([A-K0-9]{1,2}[DHCS])'

        def replace_card(match):
            card = match.group(1)
            suit = card[-1]  # Last character is the suit
            if suit in colors:
                return colors[suit] + card + reset
            return card

        return re.sub(card_pattern, replace_card, cards_string)

    try:
        print(f"Card Detection Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()

        if detected_hands:
            print(f"🃏 DETECTED CARDS ({len(detected_hands)} windows):")
            print("-" * 30)

            for hand in detected_hands:
                window_name = hand['window_name']

                # Combine player and table cards in one line
                combined_cards = ""
                if hand['player_cards_unicode']:
                    combined_cards += f"Player:{hand['player_cards_unicode']}"
                if hand['table_cards_unicode']:
                    if combined_cards:
                        combined_cards += f" Table:{hand['table_cards_unicode']}"
                    else:
                        combined_cards += f"Table:{hand['table_cards_unicode']}"

                if combined_cards:
                    colored_cards = colorize_cards(combined_cards)
                    print(f"{window_name}: {colored_cards}")
                else:
                    print(f"{window_name}: No cards detected")
        else:
            print("No cards detected in any window.")

        print()
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error printing detection results: {str(e)}")


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
                    'player_cards_unicode': format_cards(player_cards),
                    'table_cards_unicode': format_cards(table_cards),
                    'player_cards_raw': player_cards,
                    'table_cards_raw': table_cards
                })

        except Exception as e:
            print(f"    ❌ Error processing {window_name}: {str(e)}")

    return detected_cards


if __name__ == "__main__":
    print("Omaha Card Reader")
    print("------------------------------")

    WAIT_TIME = 20

    # Initialize PlayerCardReader
    print("🎯 Initializing Card Reader...")
    try:
        player_templates = load_templates("resources/templates/player_cards/")
        table_templates = load_templates("resources/templates/table_cards/")

        try:
            while True:
                session_timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
                # Create timestamped output folder using provided timestamp
                working_dir = os.getcwd()
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