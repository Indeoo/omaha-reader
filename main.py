import cv2

from src.player_card_reader import PlayerCardReader, write_summary
from src.table_card_reader import TableCardReader
from src.utils.result_processor import process_results

if __name__ == "__main__":
    imagePath = "resources/screenshots/img.png"
    templates_dir = "resources/templates/full_cards"
    image = cv2.imread(imagePath)
    table_card_reader = TableCardReader(template_dir=templates_dir)
    readed_cards = table_card_reader.read(image)
    process_results(readed_cards, "table", image=image, detector=table_card_reader)


if __name__ == "__main__":
    imagePath = "resources/screenshots/02_Lobby_exe__0_02__0_05_Pot_Limit_Omaha.png"
    templates_dir = "resources/templates/hand_cards/"
    image = cv2.imread(imagePath)
    player_card_reader = PlayerCardReader(templates_dir=templates_dir)

    readed_cards = player_card_reader.read(image)

    # Extract regions for each detection
    summary = write_summary(readed_cards, readed_cards, player_card_reader)

    # Create visualization
    result_image = player_card_reader.draw_detected_cards(image, readed_cards)

    readed_cards = {
        'original': image,
        'result_image': result_image,
        'detections': readed_cards,
        'summary': summary
    }

    process_results(readed_cards, "player", debug=True)