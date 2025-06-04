import cv2

from src.player_card_reader import PlayerCardReader
from src.readed_card import write_summary
from src.utils.result_processor import process_results

if __name__ == "__main__":
    # Player card reading
    imagePath = "resources/screenshots/img.png"
    templates_dir = "resources/templates/player_cards/"
    image = cv2.imread(imagePath)
    player_card_reader = PlayerCardReader(templates_dir=templates_dir)
    readed_cards = player_card_reader.read(image)

    # Write summary
    write_summary(readed_cards)
    # Create visualization
    result_image = player_card_reader.draw_detected_cards(image, readed_cards)

    process_results(readed_cards, original_image=image, result_image=result_image, card_type="cards")
