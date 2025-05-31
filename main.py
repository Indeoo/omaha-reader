import os

import cv2

from src.poker_hand_detector import test_template_first_detection, save_detected_cards_template_first
from src.table_card_detector import test_table_card_detection
from src.template_validator import extract_card, validate_detected_cards


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


# Usage example:
if __name__ == "__main__":
    imagePath = "resources/screenshots/img.png"
    image = cv2.imread(imagePath)

    detected_table_cards, result_image = test_table_card_detection(imagePath)
    save_detected_cards(image, detected_table_cards)
    validation_results = validate_detected_cards(image, detected_table_cards)


# if __name__ == "__main__":
#     # Test with image
#     image_path = "resources/screenshots/img.png"
#     templates_dir = "resources/templates/hand_cards/"
#
#     results = test_template_first_detection(image_path, templates_dir)
#
#     if results:
#         # Save detected cards
#         save_detected_cards_template_first(results)
#
#         # Optional: Display results (if running in environment with display)
#         try:
#             import matplotlib.pyplot as plt
#
#             plt.figure(figsize=(15, 10))
#
#             # Original image
#             plt.subplot(2, 3, 1)
#             plt.imshow(cv2.cvtColor(results['original'], cv2.COLOR_BGR2RGB))
#             plt.title('Original Image')
#             plt.axis('off')
#
#             # Hand region
#             plt.subplot(2, 3, 2)
#             plt.imshow(cv2.cvtColor(results['hand_region'], cv2.COLOR_BGR2RGB))
#             plt.title('Hand Region')
#             plt.axis('off')
#
#             # Processed
#             plt.subplot(2, 3, 3)
#             plt.imshow(results['processed'], cmap='gray')
#             plt.title('Preprocessed')
#             plt.axis('off')
#
#             # Final result
#             plt.subplot(2, 3, 4)
#             plt.imshow(cv2.cvtColor(results['result_image'], cv2.COLOR_BGR2RGB))
#             plt.title('Detected Cards with Matches')
#             plt.axis('off')
#
#             # Individual card examples
#             cards = results['detected_cards']
#             for i, card in enumerate(cards[:2]):  # Show first 2 cards
#                 plt.subplot(2, 3, 5 + i)
#                 card_img = card['card_region']
#                 plt.imshow(cv2.cvtColor(card_img, cv2.COLOR_BGR2RGB))
#                 match_name = card['template_match']['match'] or 'Unknown'
#                 score = card['template_match']['score']
#                 plt.title(f'{match_name} ({score:.2f})')
#                 plt.axis('off')
#
#             plt.tight_layout()
#             plt.show()
#
#         except ImportError:
#             print("Matplotlib not available for display")


if __name__ == "__main__":
    image_path = "resources/screenshots/02_HM3HudProcess_exe_ptTableCover.png"
    templates_dir = "resources/templates/hand_cards/"

    # Test template-first detection
    results = test_template_first_detection(image_path, templates_dir)

    if results:
        # Save detected cards
        save_detected_cards_template_first(results)

        # Optional: Display results
        try:
            import matplotlib.pyplot as plt

            plt.figure(figsize=(15, 8))

            # Original image
            plt.subplot(1, 2, 1)
            plt.imshow(cv2.cvtColor(results['original'], cv2.COLOR_BGR2RGB))
            plt.title('Original Image')
            plt.axis('off')

            # Result with detections
            plt.subplot(1, 2, 2)
            plt.imshow(cv2.cvtColor(results['result_image'], cv2.COLOR_BGR2RGB))
            plt.title(f"Detections ({results['summary']['total']} found)")
            plt.axis('off')

            plt.tight_layout()
            plt.show()

        except ImportError:
            print("Matplotlib not available for display")