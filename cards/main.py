import os

import cv2
import numpy as np
from matplotlib import pyplot as plt

from cards.hand_card_detector import HandCardDetector
from cards.table_card_detector import test_card_detection, PokerCardDetector
from cards.template_validator import validate_detected_cards, extract_card


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

    # Save hand cards
    for i, card in enumerate(detected_cards['hand_cards']):
        card_region = extract_card(image, card)  # Using the extract_card function from earlier
        filename = f"{output_dir}/hand_card_{i + 1}.png"
        cv2.imwrite(filename, card_region)
        print(f"Saved: {filename}")

    # Save table cards
    for i, card in enumerate(detected_cards['table_cards']):
        card_region = extract_card(image, card)
        filename = f"{output_dir}/table_card_{i + 1}.png"
        cv2.imwrite(filename, card_region)
        print(f"Saved: {filename}")


# Usage example:
if __name__ == "__main__":
    # Test with sample image
    # Your existing code:
    detected_cards, result_image = test_card_detection("screenshots/img.png")

    # Load the original image and validate:
    image = cv2.imread("screenshots/img.png")

    save_detected_cards(image, detected_cards)

    validation_results = validate_detected_cards(image, detected_cards)
    # To use with your own image:
    # detected_cards, result_image = test_card_detection("path/to/your/poker_image.jpg")

    detector = HandCardDetector(
        hand_card_area_range=(800, 6000),  # Smaller area range for hand cards
        aspect_ratio_range=(0.55, 0.85),  # Standard card proportions
        min_card_width=15,
        min_card_height=25
    )

    hand_cards = detector.detect_hand_cards(image)

    # Print card details
    for i, card in enumerate(hand_cards):
        print(f"Hand card {i + 1}: area={card['area']:.0f}, center={card['center']}, "
              f"size={card['width']}x{card['height']}, aspect_ratio={card['aspect_ratio']:.2f}")

    # Draw results
    result_image = detector.draw_detected_hand_cards(image, hand_cards)


def test_hand_card_detection(image_path: str = None):
    """
    Test the hand card detection system
    """
    # Initialize detector with parameters tuned for hand cards
    detector = HandCardDetector(
        hand_card_area_range=(800, 6000),  # Smaller area range for hand cards
        aspect_ratio_range=(0.55, 0.85),  # Standard card proportions
        min_card_width=15,
        min_card_height=25
    )

    if image_path:
        # Load image from file
        image = cv2.imread(image_path)
        if image is None:
            print(f"Could not load image from {image_path}")
            return None, None
    else:
        # Create a sample image with small rectangles for testing
        image = np.ones((600, 800, 3), dtype=np.uint8) * 50

        # Draw sample hand cards (smaller rectangles)
        # Card 1
        cv2.rectangle(image, (98, 400), (148, 520), (255, 255, 255), 2)  # Border
        cv2.rectangle(image, (100, 402), (146, 518), (200, 200, 255), -1)  # Card content

        # Card 2
        cv2.rectangle(image, (158, 400), (208, 520), (255, 255, 255), 2)  # Border
        cv2.rectangle(image, (160, 402), (206, 518), (200, 255, 200), -1)  # Card content

        # Card 3 (slightly rotated for testing)
        pts = np.array([[220, 405], [270, 400], [275, 520], [225, 525]], np.int32)
        cv2.fillPoly(image, [pts], (255, 200, 200))
        cv2.polylines(image, [pts], True, (255, 255, 255), 2)

        # Card 4
        cv2.rectangle(image, (288, 400), (338, 520), (255, 255, 255), 2)  # Border
        cv2.rectangle(image, (290, 402), (336, 518), (255, 255, 200), -1)  # Card content

    # Detect hand cards
    hand_cards = detector.detect_hand_cards(image)

    # Print results
    print(f"Detected {len(hand_cards)} hand cards")

    # Print card details
    for i, card in enumerate(hand_cards):
        print(f"Hand card {i + 1}: area={card['area']:.0f}, center={card['center']}, "
              f"size={card['width']}x{card['height']}, aspect_ratio={card['aspect_ratio']:.2f}")

    # Draw results
    result_image = detector.draw_detected_hand_cards(image, hand_cards)

    # Display results
    try:
        plt.figure(figsize=(15, 10))

        # Show original image
        plt.subplot(2, 3, 1)
        plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        plt.title('Original Image')
        plt.axis('off')

        # Show preprocessed image
        plt.subplot(2, 3, 2)
        processed = detector.preprocess_image_for_hands(image)
        plt.imshow(processed, cmap='gray')
        plt.title('Preprocessed (Edge Detection)')
        plt.axis('off')

        # Show detected cards
        plt.subplot(2, 3, 3)
        plt.imshow(cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB))
        plt.title(f'Detected Hand Cards ({len(hand_cards)})')
        plt.axis('off')

        # Show individual extracted cards
        if hand_cards:
            for i, card in enumerate(hand_cards[:3]):  # Show first 3 cards
                plt.subplot(2, 3, 4 + i)
                extracted_card = detector.extract_hand_card_region(image, card)
                plt.imshow(cv2.cvtColor(extracted_card, cv2.COLOR_BGR2RGB))
                plt.title(f'Card {i + 1}')
                plt.axis('off')

        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"Display not available: {e}")
        print("But detection completed successfully")

    return hand_cards, result_image


# Example of using both detectors together
def detect_all_cards(image_path: str):
    """
    Use both table and hand card detectors together
    """

    # Initialize both detectors
    table_detector = PokerCardDetector()
    hand_detector = HandCardDetector()

    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Could not load image from {image_path}")
        return

    # Detect table cards
    table_results = table_detector.detect_cards(image)
    table_cards = table_results['table_cards']

    # Detect hand cards
    hand_cards = hand_detector.detect_hand_cards(image)

    # Combine results
    print(f"Total cards detected:")
    print(f"  Table cards: {len(table_cards)}")
    print(f"  Hand cards: {len(hand_cards)}")

    # Draw all cards on one image
    result_image = image.copy()

    # Draw table cards in red
    for card in table_cards:
        cv2.drawContours(result_image, [card['box_points']], -1, (0, 0, 255), 2)
        cv2.putText(result_image, 'Table', card['center'],
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # Draw hand cards in green
    result_image = hand_detector.draw_detected_hand_cards(result_image, hand_cards)

    return {
        'table_cards': table_cards,
        'hand_cards': hand_cards,
        'result_image': result_image
    }
