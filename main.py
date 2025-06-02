import cv2

from src.player_card_reader import detect_by_template, process_results
from src.table_card_reader import test_table_card_detection
from src.utils.save_utils import save_detected_cards
from src.utils.template_validator import validate_detected_cards


# Usage example:
# if __name__ == "__main__":
#     imagePath = "resources/screenshots/img.png"
#     image = cv2.imread(imagePath)
#
#     detected_table_cards, result_image = test_table_card_detection(image)
#     save_detected_cards(image, detected_table_cards)
#     validation_results = validate_detected_cards(image, detected_table_cards)



if __name__ == "__main__":
    imagePath = "resources/screenshots/02_Lobby_exe__0_02__0_05_Pot_Limit_Omaha.png"
    templates_dir = "resources/templates/hand_cards/"
    image = cv2.imread(imagePath)

    # Test template-first detection
    detected_cards = detect_by_template(image, templates_dir)
    process_results(detected_cards, debug=True)