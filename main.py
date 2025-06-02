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


#
# if __name__ == "__main__":
#     # Table card reading
#     imagePath = "resources/screenshots/img.png"
#     templates_dir = "resources/templates/full_cards"
#     image = cv2.imread(imagePath)
#     table_card_reader = TableCardReader(template_dir=templates_dir)
#     readed_cards = table_card_reader.read(image)
#
#     # Convert ReadedCard objects back to old format for process_results
#     old_format_cards = []
#     for card in readed_cards:
#         old_format_cards.append({
#             'contour': card.contour,
#             'bounding_rect': card.bounding_rect,
#             'rotated_rect': card.rotated_rect,
#             'box_points': card.box_points,
#             'area': card.area,
#             'center': card.center
#         })
#
#     process_results(old_format_cards, "table", image=image, detector=table_card_reader)

if __name__ == "__main__":
    # Player card reading
    imagePath = "resources/screenshots/02_Lobby_exe__0_02__0_05_Pot_Limit_Omaha.png"
    templates_dir = "resources/templates/hand_cards/"
    image = cv2.imread(imagePath)
    player_card_reader = PlayerCardReader(templates_dir=templates_dir)

    readed_cards = player_card_reader.read(image)

    # Write summary
    summary = write_summary(readed_cards, player_card_reader)

    # Create visualization
    result_image = player_card_reader.draw_detected_cards(image, readed_cards)

    # Convert to old format for process_results
    old_format_results = {
        'original': image,
        'result_image': result_image,
        'detections': [
            {
                'template_name': card.template_name,
                'match_score': card.match_score,
                'bounding_rect': card.bounding_rect,
                'center': card.center,
                'scale': card.scale,
                'card_region': card.card_region,
                'area': card.area,
                'aspect_ratio': card.bounding_rect[2] / card.bounding_rect[3] if card.bounding_rect[3] > 0 else 0
            } for card in readed_cards
        ],
        'summary': summary
    }

    process_results(old_format_results, "player", debug=True)
