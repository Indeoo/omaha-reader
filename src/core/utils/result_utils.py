import os
from datetime import datetime
from src.core.domain.readed_card import ReadedCard
from src.core.domain.detection_result import DetectionResult


def print_detection_result(result: DetectionResult):
    """
    Print detection result for a single processed result to console with colored cards

    Args:
        result: DetectionResult object
    """
    try:
        # Format the output line
        line = _format_detection_output(result)
        print(f"  🃏 {line}")

        # Print summary
        details = []
        if result.player_cards:
            details.append(f"{len(result.player_cards)} player cards")
        if result.table_cards:
            details.append(f"{len(result.table_cards)} table cards")
        if result.positions:
            details.append(f"{len(result.positions)} positions")

        if details:
            print(f"     ({', '.join(details)})")
        elif not result.has_cards:
            print(f"  🃏 No cards detected")

    except Exception as e:
        print(f"  ❌ Error printing detection result: {str(e)}")


def _format_detection_output(result: DetectionResult) -> str:
    """
    Generate the detection output from a processed result with ANSI colors

    Args:
        result: DetectionResult object

    Returns:
        Formatted string with ANSI colors for console display
    """
    window_name = result.window_name

    combined_cards = ""
    if result.player_cards:
        player_cards_colored = ReadedCard.format_cards_ansi(result.player_cards)
        combined_cards += f"Player:{player_cards_colored}"

    if result.table_cards:
        table_cards_colored = ReadedCard.format_cards_ansi(result.table_cards)
        if combined_cards:
            combined_cards += f" Table:{table_cards_colored}"
        else:
            combined_cards += f"Table:{table_cards_colored}"

    if combined_cards:
        return f"{window_name}: {combined_cards}"
    else:
        return f"{window_name}: No cards detected"


def write_combined_result(result: DetectionResult, timestamp_folder: str, filename: str, index: int):
    """
    Write detection and position results for a single image to one file

    Args:
        result: DetectionResult object containing all detection info
        timestamp_folder: Path to the timestamp folder where file should be saved
        filename: Name of the file to save (e.g., "detection_20240116_143052_123.txt")
        index: Image index for reference
    """
    combined_file_path = os.path.join(timestamp_folder, filename)

    try:
        with open(combined_file_path, 'w', encoding='utf-8') as f:
            # Write header
            _write_file_header(f, result, index)

            # Write card detection section
            _write_card_detection_section(f, result)

            # Write position detection section
            _write_position_detection_section(f, result)

            f.write("\n" + "=" * 60 + "\n")

    except Exception as e:
        print(f"  ❌ Error writing combined result to {filename}: {str(e)}")


def _write_file_header(f, result: DetectionResult, index: int):
    """Write file header section"""
    f.write(f"Combined Detection & Position Result - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("=" * 60 + "\n\n")

    # Window information
    f.write(f"Window: {result.window_name}\n")
    f.write(f"Source File: {result.filename}\n")
    f.write(f"Image Index: {index}\n")
    f.write("-" * 30 + "\n\n")


def _write_card_detection_section(f, result: DetectionResult):
    """Write card detection section to file"""
    f.write("🃏 CARD DETECTION:\n")
    f.write("=" * 30 + "\n")

    if result.has_cards:
        # Format detected cards (simple template names for file output)
        line = _format_detection_output_simple(result)
        f.write(f"{line}\n\n")

        # Add detailed card information
        f.write("📊 CARD DETAILS:\n")
        f.write("-" * 20 + "\n")

        if result.player_cards:
            f.write(f"\nPlayer Cards ({len(result.player_cards)} cards):\n")
            for i, card in enumerate(result.player_cards, 1):
                f.write(f"  {i}. {card.template_name}: score={card.match_score:.3f}, center={card.center}\n")

        if result.table_cards:
            f.write(f"\nTable Cards ({len(result.table_cards)} cards):\n")
            for i, card in enumerate(result.table_cards, 1):
                f.write(f"  {i}. {card.template_name}: score={card.match_score:.3f}, center={card.center}\n")

        if not result.player_cards and not result.table_cards:
            f.write("  No cards detected in this image.\n")
    else:
        f.write("No card detection performed for this image.\n")

    f.write("\n")


def _write_position_detection_section(f, result: DetectionResult):
    """Write position detection section to file"""
    f.write("🎯 POSITION DETECTION:\n")
    f.write("=" * 30 + "\n")

    f.write(f"Detected Positions: {len(result.positions)} found\n")
    f.write("-" * 20 + "\n")

    if result.positions:
        position_names = ", ".join([p.position_name for p in result.positions])
        f.write(f"Positions: {position_names}\n\n")

        f.write("📊 POSITION DETAILS:\n")
        f.write("-" * 20 + "\n")
        for i, pos in enumerate(result.positions, 1):
            f.write(f"\n{i}. {pos.position_name}:\n")
            f.write(f"   Center: {pos.center}\n")
            f.write(f"   Score: {pos.match_score:.3f}\n")
            f.write(f"   Bounding Box: {pos.bounding_rect}\n")
    else:
        f.write("No positions detected in this image.\n")


def _format_detection_output_simple(result: DetectionResult) -> str:
    """
    Generate simple detection output without colors (for file output)

    Args:
        result: DetectionResult object

    Returns:
        Formatted string without colors
    """
    window_name = result.window_name

    combined_cards = ""
    if result.player_cards:
        player_cards_str = ReadedCard.format_cards_simple(result.player_cards)
        combined_cards += f"Player:{player_cards_str}"

    if result.table_cards:
        table_cards_str = ReadedCard.format_cards_simple(result.table_cards)
        if combined_cards:
            combined_cards += f" Table:{table_cards_str}"
        else:
            combined_cards += f"Table:{table_cards_str}"

    if combined_cards:
        return f"{window_name}: {combined_cards}"
    else:
        return f"{window_name}: No cards detected"