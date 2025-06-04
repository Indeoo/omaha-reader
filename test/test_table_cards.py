import cv2

from src.readed_card import write_summary
from src.table_card_reader import TableCardReader
from src.utils.result_processor import process_results


if __name__ == "__main__":
    # Table card reading
    imagePath = "resources/screenshots/img.png"
    templates_dir = "resources/templates/full_cards"
    image = cv2.imread(imagePath)
    table_card_reader = TableCardReader(template_dir=templates_dir)
    readed_cards = table_card_reader.read(image)

    # Write summary
    write_summary(readed_cards)

    result_image = table_card_reader.draw_detected_cards(image, readed_cards)

    process_results(readed_cards, original_image=image, result_image=result_image, card_type="cards")
