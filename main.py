import cv2

from src.player_card_reader import read_player_cards
from src.table_card_reader import read_table_card


# if __name__ == "__main__":
#     imagePath = "resources/screenshots/img.png"
#     templates_dir = "resources/templates/full_cards"
#     image = cv2.imread(imagePath)
#
#     read_table_card(image, "resources/templates/full_cards")

if __name__ == "__main__":
    imagePath = "resources/screenshots/02_Lobby_exe__0_02__0_05_Pot_Limit_Omaha.png"
    templates_dir = "resources/templates/hand_cards/"
    image = cv2.imread(imagePath)

    readed_cards = read_player_cards(image, templates_dir)
