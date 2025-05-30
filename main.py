import os

import cv2

from src.hand_card_detector import test_hand_card_detection
from src.template_validator import extract_card


def save_detected_cards(image, detected_cards, output_dir="detected_cards"):
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


# Usage example:
if __name__ == "__main__":
    imagePath = "screenshots/img.png"
    image = cv2.imread(imagePath)

    # detected_table_cards, result_image = test_table_card_detection(imagePath)
    # save_detected_cards(image, detected_table_cards)
    # validation_results = validate_detected_cards(image, detected_table_cards)



    results = test_hand_card_detection(imagePath)
