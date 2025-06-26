import os

from datetime import datetime
from typing import Dict

from src.domain.readed_card import ReadedCard


def print_detection_result(detected_hand: Dict):
    """
    Print detection result for a single image to console with colored cards

    Args:
        detected_hand: Detection result for a single window/image
    """

    def colorize_cards(cards_string: str) -> str:
        """Apply color to cards based on suit"""
        if not cards_string:
            return cards_string

        # ANSI color codes
        colors = {
            'D': '\033[94m',  # Bright Blue for Diamonds
            'H': '\033[91m',  # Bright Red for Hearts
            'C': '\033[92m',  # Bright Green for Clubs
            'S': '\033[90m',  # Bright Black (Dark Gray) for Spades
        }
        reset = '\033[0m'

        import re
        card_pattern = r'([A-K0-9]{1,2}[DHCS])'

        def replace_card(match):
            card = match.group(1)
            suit = card[-1]
            if suit in colors:
                return colors[suit] + card + reset
            return card

        return re.sub(card_pattern, replace_card, cards_string)

    try:
        line = format_detection_output_single(detected_hand)
        colored_line = colorize_cards(line)
        print(f"  🃏 {colored_line}")

        # Print summary
        player_cards = detected_hand.get('player_cards_raw', [])
        table_cards = detected_hand.get('table_cards_raw', [])

        details = []
        if player_cards:
            details.append(f"{len(player_cards)} player cards")
        if table_cards:
            details.append(f"{len(table_cards)} table cards")

        if details:
            print(f"     ({', '.join(details)})")

    except Exception as e:
        print(f"  ❌ Error printing detection result: {str(e)}")


def format_detection_output_single(detected_hand: Dict) -> str:
    """Generate the detection output for a single hand"""
    window_name = detected_hand['window_name']

    combined_cards = ""
    if detected_hand.get('player_cards_raw'):
        combined_cards += f"Player:{ReadedCard.format_cards(detected_hand['player_cards_raw'])}"
    if detected_hand.get('table_cards_raw'):
        if combined_cards:
            combined_cards += f" Table:{ReadedCard.format_cards(detected_hand['table_cards_raw'])}"
        else:
            combined_cards += f"Table:{ReadedCard.format_cards(detected_hand['table_cards_raw'])}"

    if combined_cards:
        return f"{window_name}: {combined_cards}"
    else:
        return f"{window_name}: No cards detected"


# New combined function to add to src/utils/result_utils.py
def write_combined_result(card_result: Dict, position_result: Dict, timestamp_folder: str, filename: str):
    """
    Write both detection and position results for a single image to one file

    Args:
        card_result: Detection result for a single window/image (can be None)
        position_result: Position result for a single window/image (can be None)
        timestamp_folder: Path to the timestamp folder where file should be saved
        filename: Name of the file to save (e.g., "results_20240116_143052_123.txt")
    """
    combined_file_path = os.path.join(timestamp_folder, filename)

    try:
        with open(combined_file_path, 'w', encoding='utf-8') as f:
            f.write(f"Combined Detection & Position Result - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")

            # Window information (use card_result or position_result as available)
            result_info = card_result or position_result
            if result_info:
                f.write(f"Window: {result_info['window_name']}\n")
                f.write(f"Source File: {result_info['filename']}\n")
                f.write(f"Image Index: {result_info['image_index']}\n")
                f.write("-" * 30 + "\n\n")

            # ========== CARD DETECTION SECTION ==========
            f.write("🃏 CARD DETECTION:\n")
            f.write("=" * 30 + "\n")

            if card_result:
                # Format detected cards
                line = format_detection_output_single(card_result)
                f.write(f"{line}\n\n")

                # Add detailed card information
                f.write("📊 CARD DETAILS:\n")
                f.write("-" * 20 + "\n")

                player_cards = card_result.get('player_cards_raw', [])
                table_cards = card_result.get('table_cards_raw', [])

                if player_cards:
                    f.write(f"\nPlayer Cards ({len(player_cards)} cards):\n")
                    for i, card in enumerate(player_cards, 1):
                        f.write(f"  {i}. {card.template_name}: score={card.match_score:.3f}, center={card.center}\n")

                if table_cards:
                    f.write(f"\nTable Cards ({len(table_cards)} cards):\n")
                    for i, card in enumerate(table_cards, 1):
                        f.write(f"  {i}. {card.template_name}: score={card.match_score:.3f}, center={card.center}\n")

                if not player_cards and not table_cards:
                    f.write("  No cards detected in this image.\n")
            else:
                f.write("No card detection performed for this image.\n")

            f.write("\n")

            # ========== POSITION DETECTION SECTION ==========
            f.write("🎯 POSITION DETECTION:\n")
            f.write("=" * 30 + "\n")

            if position_result:
                positions = position_result.get('positions', [])

                f.write(f"Detected Positions: {len(positions)} found\n")
                f.write("-" * 20 + "\n")

                if positions:
                    position_names = ", ".join([p.position_name for p in positions])
                    f.write(f"Positions: {position_names}\n\n")

                    f.write("📊 POSITION DETAILS:\n")
                    f.write("-" * 20 + "\n")
                    for i, pos in enumerate(positions, 1):
                        f.write(f"\n{i}. {pos.position_name}:\n")
                        f.write(f"   Center: {pos.center}\n")
                        f.write(f"   Score: {pos.match_score:.3f}\n")
                        f.write(f"   Bounding Box: {pos.bounding_rect}\n")
                else:
                    f.write("No positions detected in this image.\n")
            else:
                f.write("No position detection performed for this image.\n")

            f.write("\n" + "=" * 60 + "\n")

    except Exception as e:
        print(f"  ❌ Error writing combined result to {filename}: {str(e)}")

