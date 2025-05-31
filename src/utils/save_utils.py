import os

import cv2

from src.utils.template_validator import extract_card


def save_detected_cards(image, detected_cards, output_dir="resources/detected_cards"):
    """
    Save each detected card as a separate PNG file

    Args:
        image: Original image (numpy array)
        detected_cards: Output from detect_cards()
        output_dir: Directory to save the card images
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Save table cards
    for i, card in enumerate(detected_cards['table_cards']):
        card_region = extract_card(image, card)
        filename = f"{output_dir}/table_card_{i + 1}.png"
        cv2.imwrite(filename, card_region)
        print(f"Saved: {filename}")