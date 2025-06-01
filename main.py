from src.poker_hand_detector import read_hand


# Usage example:
# if __name__ == "__main__":
#     imagePath = "resources/screenshots/img.png"
#     image = cv2.imread(imagePath)
#
#     detected_table_cards, result_image = test_table_card_detection(imagePath)
#     save_detected_cards(image, detected_table_cards)
#     validation_results = validate_detected_cards(image, detected_table_cards)
#


if __name__ == "__main__":
    image_path = "resources/screenshots/02_Lobby_exe__0_02__0_05_Pot_Limit_Omaha.png"
    templates_dir = "resources/templates/hand_cards/"

    read_hand(image_path, templates_dir)