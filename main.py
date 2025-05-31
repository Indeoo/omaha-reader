import cv2

from src.poker_hand_detector import test_template_first_detection, save_detected_cards_template_first
from src.table_card_detector import test_table_card_detection
from src.utils.save_utils import save_detected_cards
from src.utils.template_validator import validate_detected_cards


# Usage example:
if __name__ == "__main__":
    imagePath = "resources/screenshots/img.png"
    image = cv2.imread(imagePath)

    detected_table_cards, result_image = test_table_card_detection(imagePath)
    save_detected_cards(image, detected_table_cards)
    validation_results = validate_detected_cards(image, detected_table_cards)



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