import os

from datetime import datetime
from typing import Dict, Union

from src.domain.readed_card import ReadedCard
from src.utils.detection_result import DetectionResult


def print_detection_result(result: Union[Dict, DetectionResult]):
    """
    Print detection result for a single processed result to console with colored cards

    Args:
        result: DetectionResult object or dictionary (for backward compatibility)
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
        # Format the output line
        line = format_detection_output_from_result(result)
        colored_line = colorize_cards(line)
        print(f"  🃏 {colored_line}")

        # Handle both DetectionResult objects and dictionaries
        if isinstance(result, DetectionResult):
            player_cards = result.player_cards
            table_cards = result.table_cards
            positions = result.positions
            has_cards = result.has_cards
        else:
            player_cards = result.get('player_cards', [])
            table_cards = result.get('table_cards', [])
            positions = result.get('positions', [])
            has_cards = result.get('has_cards', False)

        # Print summary
        details = []
        if player_cards:
            details.append(f"{len(player_cards)} player cards")
        if table_cards:
            details.append(f"{len(table_cards)} table cards")
        if positions:
            details.append(f"{len(positions)} positions")

        if details:
            print(f"     ({', '.join(details)})")
        elif not has_cards:
            print(f"  🃏 No cards detected")

    except Exception as e:
        print(f"  ❌ Error printing detection result: {str(e)}")


def format_detection_output_from_result(result: Union[Dict, DetectionResult]) -> str:
    """Generate the detection output from a processed result"""
    # Handle both DetectionResult objects and dictionaries
    if isinstance(result, DetectionResult):
        window_name = result.window_name
        player_cards = result.player_cards
        table_cards = result.table_cards
    else:
        window_name = result['window_name']
        player_cards = result.get('player_cards', [])
        table_cards = result.get('table_cards', [])

    combined_cards = ""
    if player_cards:
        combined_cards += f"Player:{ReadedCard.format_cards(player_cards)}"
    if table_cards:
        if combined_cards:
            combined_cards += f" Table:{ReadedCard.format_cards(table_cards)}"
        else:
            combined_cards += f"Table:{ReadedCard.format_cards(table_cards)}"

    if combined_cards:
        return f"{window_name}: {combined_cards}"
    else:
        return f"{window_name}: No cards detected"


def write_combined_result(result: DetectionResult, timestamp_folder: str, filename: str):
    """
    Write detection and position results for a single image to one file

    Args:
        result: DetectionResult object containing all detection info
        timestamp_folder: Path to the timestamp folder where file should be saved
        filename: Name of the file to save (e.g., "detection_20240116_143052_123.txt")
    """
    combined_file_path = os.path.join(timestamp_folder, filename)

    window_name = result.window_name
    source_filename = result.filename
    index = result.index
    has_cards = result.has_cards
    player_cards = result.player_cards
    table_cards = result.table_cards
    positions = result.positions

    try:
        with open(combined_file_path, 'w', encoding='utf-8') as f:
            f.write(f"Combined Detection & Position Result - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")

            # Window information
            f.write(f"Window: {window_name}\n")
            f.write(f"Source File: {source_filename}\n")
            f.write(f"Image Index: {index}\n")
            f.write("-" * 30 + "\n\n")

            # ========== CARD DETECTION SECTION ==========
            f.write("🃏 CARD DETECTION:\n")
            f.write("=" * 30 + "\n")

            if has_cards:
                # Format detected cards
                line = format_detection_output_from_result(result)
                f.write(f"{line}\n\n")

                # Add detailed card information
                f.write("📊 CARD DETAILS:\n")
                f.write("-" * 20 + "\n")

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

            f.write("\n" + "=" * 60 + "\n")

    except Exception as e:
        print(f"  ❌ Error writing combined result to {filename}: {str(e)}")