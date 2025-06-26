#!/usr/bin/env python3
"""
Shared image processing functions for both main.py and main_web3.py
"""
from typing import Dict, List, Callable

from src.utils.benchmark_utils import benchmark
from src.utils.detect_utils import detect_cards_single, detect_positions_single, save_detection_result_image
from src.domain.readed_card import ReadedCard
from src.utils.result_utils import print_detection_result, print_position_result, write_combined_result
from src.utils.opencv_utils import load_templates


class PokerGameProcessor:
    def __init__(
            self,
            player_templates_dir: str = None,
            table_templates_dir: str = None,
            position_templates_dir: str = None,
            player_templates: Dict = None,
            table_templates: Dict = None,
            position_templates: Dict = None,
            detect_positions: bool = True,
            save_result_images=True,
            write_detection_files=True,
    ):
        # Load templates from directories if provided
        if player_templates_dir:
            self.player_templates = load_templates(player_templates_dir)
        elif player_templates:
            self.player_templates = player_templates
        else:
            self.player_templates = {}

        if table_templates_dir:
            self.table_templates = load_templates(table_templates_dir)
        elif table_templates:
            self.table_templates = table_templates
        else:
            self.table_templates = {}

        if position_templates_dir:
            self.position_templates = load_templates(position_templates_dir)
        elif position_templates:
            self.position_templates = position_templates
        else:
            self.position_templates = {}

            self.detect_positions = detect_positions
            self.save_result_images = save_result_images
            self.write_detection_files = write_detection_files

    @benchmark
    def process_captured_images(
            self,
            captured_images: List[Dict],
            timestamp_folder: str,
            process_callback: Callable = None,
    ) -> List[Dict]:
        """
        Process a list of captured images to detect cards and optionally positions.

        Args:
            captured_images: List of captured image dictionaries
            timestamp_folder: Folder to save results
            process_callback: Optional callback function called for each processed image
                             with args (i, captured_item, card_result, position_result)

        Returns:
            List of dictionaries containing processed results for each image
        """
        processed_results = []

        for i, captured_item in enumerate(captured_images):
            window_name = captured_item['window_name']

            # Detect cards for single image
            card_result = detect_cards_single(captured_item, i, self.player_templates, self.table_templates)

            # Detect positions for single image (skip full screen)
            position_result = None
            if self.detect_positions and self.position_templates and window_name:
                position_result = detect_positions_single(captured_item, i, self.position_templates)

            # Create combined result
            result = {
                'index': i,
                'captured_item': captured_item,
                'card_result': card_result,
                'position_result': position_result,
                'window_name': window_name,
                'filename': captured_item['filename']
            }

            i = result['index']
            captured_item = result['captured_item']
            card_result = result['card_result']
            position_result = result['position_result']
            window_name = result['window_name']
            filename = result['filename']

            print(f"\n📷 Processing image {i + 1}: {window_name}")
            print("-" * 40)

            # Print detection results
            if card_result:
                print_detection_result(card_result)
            else:
                print(f"  🃏 No cards detected")

            # Print position results
            if position_result:
                print_position_result(position_result)

            # Write result file
            if self.write_detection_files:
                result_filename = f"detection_{filename}.txt"
                write_combined_result(card_result, position_result, timestamp_folder, result_filename)

            # Save result image
            if self.save_result_images:
                save_detection_result_image(
                    timestamp_folder,
                    captured_item,
                    card_result,
                    position_result
                )

            processed_results.append(result)

            # Call callback if provided
            if process_callback:
                process_callback(i, captured_item, card_result, position_result)

        return processed_results


def format_results_for_web(processed_results: List[Dict]) -> List[Dict]:
    """
    Format results for web-based application (main_web3.py)

    Args:
        processed_results: List of processed result dictionaries

    Returns:
        List of formatted detections for web display
    """
    detections = []

    for result in processed_results:
        card_result = result['card_result']
        window_name = result['window_name']

        if card_result:
            # Extract cards
            player_cards = card_result.get('player_cards_raw', [])
            table_cards = card_result.get('table_cards_raw', [])

            detection = {
                'window_name': window_name,
                'player_cards': format_cards_for_web(player_cards),
                'table_cards': format_cards_for_web(table_cards),
                'player_cards_string': ReadedCard.format_cards(player_cards),
                'table_cards_string': ReadedCard.format_cards(table_cards)
            }

            if detection['player_cards'] or detection['table_cards']:
                detections.append(detection)

    return detections


def format_cards_for_web(cards: List) -> List[Dict]:
    """Format cards for web display with suit symbols"""
    if not cards:
        return []

    formatted = []
    for card in cards:
        if card.template_name:
            formatted.append({
                'name': card.template_name,
                'display': format_card_with_unicode(card.template_name),
                'score': round(card.match_score, 3) if card.match_score else 0
            })
    return formatted


def format_card_with_unicode(card_name: str) -> str:
    """Convert card name to include Unicode suit symbols"""
    if not card_name or len(card_name) < 2:
        return card_name

    # Unicode suit symbols mapping
    suit_unicode = {
        'S': '♠',  # Spades
        'H': '♥',  # Hearts
        'D': '♦',  # Diamonds
        'C': '♣'  # Clubs
    }

    # Get the last character as suit
    suit = card_name[-1].upper()
    rank = card_name[:-1]

    if suit in suit_unicode:
        return f"{rank}{suit_unicode[suit]}"
    else:
        return card_name
