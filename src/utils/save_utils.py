import os
from datetime import datetime

import cv2
from typing import List
from src.readed_card import ReadedCard


def save_detected_cards(readed_cards: List[ReadedCard], output_dir="resources/detected_cards"):
    """
    Save each detected card as a separate PNG file

    Args:
        readed_cards: List of ReadedCard objects
        output_dir: Directory to save the card images
    """
    os.makedirs(output_dir, exist_ok=True)

    for i, card in enumerate(readed_cards):
        filename = os.path.join(output_dir, f"table_card_{i + 1}.png")
        cv2.imwrite(filename, card.card_region)
        print(f"Saved: {filename}")


def save_readed_player_cards(readed_cards: List[ReadedCard], output_dir=f"resources/player_cards_readed/{datetime.now().strftime("%Y%m%d_%H%M%S")}"):
    """Save each detected card region"""
    os.makedirs(output_dir, exist_ok=True)

    for i, card in enumerate(readed_cards):
        template_name = card.template_name
        confidence = card.match_score
        scale = card.scale if card.scale else 1.0

        filename = os.path.join(output_dir, f"{template_name}_conf{confidence:.2f}_scale{scale:.1f}_{i}.png")
        cv2.imwrite(filename, card.card_region)
        print(f"Saved: {filename}")