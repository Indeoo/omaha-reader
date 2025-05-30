import cv2

from cards.poker_card_detector import test_card_detection
from cards.template_validator import validate_detected_cards

# Usage example:
if __name__ == "__main__":
    # Test with sample image
    # Your existing code:
    detected_cards, result_image = test_card_detection("screenshots/img.png")

    # Load the original image and validate:
    image = cv2.imread("screenshots/img.png")
    validation_results = validate_detected_cards(image, detected_cards)



    # To use with your own image:
    # detected_cards, result_image = test_card_detection("path/to/your/poker_image.jpg")