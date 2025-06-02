import cv2

from src.player_card_reader import PlayerCardReader
from src.table_card_reader import TableCardReader
from src.utils.result_processor import process_results


def write_summary(readed_cards, player_card_reader):
    # Get summary
    summary = player_card_reader.get_detection_summary(readed_cards)
    print(f"\nDetection Summary:")
    print(f"Total detections: {summary['total']}")
    print(f"Average confidence: {summary['average_confidence']:.3f}")
    print(f"Scales used: {summary['scales_used']}")
    print(f"Cards found: {summary['cards']}")
    # Print detailed results
    print(f"\nDetailed Results:")
    for i, card in enumerate(readed_cards):
        print(f"  Detection {i + 1}:")
        print(f"    Template: {card.template_name}")
        print(f"    Confidence: {card.match_score:.3f}")
        print(f"    Position: {card.center}")
        print(f"    Size: {card.bounding_rect[2:4]}")
        print(f"    Scale: {card.scale:.1f}")
        print()
    return summary


if __name__ == "__main__":
    # Table card reading
    imagePath = "resources/screenshots/img.png"
    templates_dir = "resources/templates/full_cards"
    image = cv2.imread(imagePath)
    table_card_reader = TableCardReader(template_dir=templates_dir)
    readed_cards = table_card_reader.read(image)

    result_image = table_card_reader.draw_detected_cards(image, readed_cards)

    process_results(readed_cards, "table", image=image, detector=table_card_reader)

# if __name__ == "__main__":
#     # Player card reading
#     imagePath = "resources/screenshots/02_Lobby_exe__0_02__0_05_Pot_Limit_Omaha.png"
#     templates_dir = "resources/templates/player_cards/"
#     image = cv2.imread(imagePath)
#     player_card_reader = PlayerCardReader(templates_dir=templates_dir)
#     readed_cards = player_card_reader.read(image)
#
#     # Write summary
#     summary = write_summary(readed_cards, player_card_reader)
#     # Create visualization
#     result_image = player_card_reader.draw_detected_cards(image, readed_cards)
#
#     process_results(readed_cards, "player", debug=True, original_image=image, result_image=result_image)
