import os
from datetime import datetime
from typing import List, Dict

from src.domain.readed_card import ReadedCard


def format_detection_output(detected_hands):
    """Generate the core detection data structure"""
    lines = []
    for hand in detected_hands:
        window_name = hand['window_name']

        combined_cards = ""
        if hand['player_cards_raw']:
            combined_cards += f"Player:{ReadedCard.format_cards(hand['player_cards_raw'])}"
        if hand['table_cards_raw']:
            if combined_cards:
                combined_cards += f" Table:{ReadedCard.format_cards(hand['table_cards_raw'])}"
            else:
                combined_cards += f"Table:{ReadedCard.format_cards(hand['table_cards_raw'])}"

        if combined_cards:
            lines.append(f"{window_name}: {combined_cards}")
        else:
            lines.append(f"{window_name}: No cards detected")

    return lines


def write_detection_results(detected_hands: List[dict], timestamp_folder: str):
    """
    Write detection results to detection.txt in the timestamp folder

    Args:
        detected_hands: List of detected hands with window names and card data
        timestamp_folder: Path to the timestamp folder where detection.txt should be saved
    """
    detection_file_path = os.path.join(timestamp_folder, "detection.txt")
    lines = format_detection_output(detected_hands)

    try:
        with open(detection_file_path, 'w', encoding='utf-8') as f:
            f.write(f"Card Detection Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")

            if detected_hands:
                f.write(f"🃏 DETECTED CARDS ({len(detected_hands)} windows):\n")
                f.write("-" * 30 + "\n")

                for line in lines:
                    f.write(f"{line}\n")
            else:
                f.write("No cards detected in any window.\n")

            f.write("\n" + "=" * 60 + "\n")

    except Exception as e:
        print(f"❌ Error writing detection results: {str(e)}")


def print_detection_results(detected_hands: List[dict]):
    """
    Print detection results to console with colored cards based on suit

    Args:
        detected_hands: List of detected hands with window names and card data
    """

    def colorize_cards(cards_string: str) -> str:
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

    lines = format_detection_output(detected_hands)

    try:
        print(f"Card Detection Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()

        if detected_hands:
            print(f"🃏 DETECTED CARDS ({len(detected_hands)} windows):")
            print("-" * 30)

            for line in lines:
                colored_line = colorize_cards(line)
                print(colored_line)
        else:
            print("No cards detected in any window.")

        print()
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error printing detection results: {str(e)}")


def write_position_results(position_results: List[Dict], timestamp_folder: str):
    """
    Write position detection results to positions.txt in the timestamp folder

    Args:
        position_results: List of dicts with window names and detected positions
        timestamp_folder: Path to the timestamp folder where positions.txt should be saved
    """
    positions_file_path = os.path.join(timestamp_folder, "positions.txt")

    try:
        with open(positions_file_path, 'w', encoding='utf-8') as f:
            f.write(f"Position Detection Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")

            if position_results:
                f.write(f"🎯 DETECTED POSITIONS ({len(position_results)} windows):\n")
                f.write("-" * 30 + "\n")

                for result in position_results:
                    window_name = result['window_name']
                    positions = result['positions']

                    if positions:
                        position_names = ", ".join([p.position_name for p in positions])
                        f.write(f"{window_name}: {position_names}\n")

                        # Write detailed info
                        f.write("  Details:\n")
                        for pos in positions:
                            f.write(f"    - {pos.position_name}: center={pos.center}, score={pos.match_score:.3f}\n")
                    else:
                        f.write(f"{window_name}: No positions detected\n")

                    f.write("\n")
            else:
                f.write("No positions detected in any window.\n")

            f.write("\n" + "=" * 60 + "\n")

    except Exception as e:
        print(f"❌ Error writing position results: {str(e)}")


def print_position_results(position_results: List[Dict]):
    """
    Print position detection results to console

    Args:
        position_results: List of dicts with window names and detected positions
    """
    print("\n🎯 PLAYER POSITIONS:")
    print("-" * 30)

    if position_results:
        for result in position_results:
            window_name = result['window_name']
            positions = result['positions']

            if positions:
                position_names = ", ".join([p.position_name for p in positions])
                print(f"{window_name}: {position_names}")
            else:
                print(f"{window_name}: No positions detected")
    else:
        print("No positions detected in any window.")

    print("-" * 30)