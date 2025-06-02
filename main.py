import cv2

from src.player_card_reader import read_player_cards
from src.table_card_reader import TableCardReader
from src.utils.result_processor import process_results

if __name__ == "__main__":
    imagePath = "resources/screenshots/img.png"
    templates_dir = "resources/templates/full_cards"
    image = cv2.imread(imagePath)

    table_card_reader = TableCardReader(
        (1000, 25000),  # Larger cards
        (0.5, 0.85),  # Typical card proportions
        templates_dir
    )

    readed_cards = table_card_reader.read(image)
    process_results(readed_cards, "table", image=image, detector=table_card_reader)


if __name__ == "__main__":
    imagePath = "resources/screenshots/02_Lobby_exe__0_02__0_05_Pot_Limit_Omaha.png"
    templates_dir = "resources/templates/hand_cards/"
    image = cv2.imread(imagePath)

    read_player_cards(image, templates_dir)
