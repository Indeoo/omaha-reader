import os
import cv2


def save_detected_cards(extracted_cards, output_dir="resources/detected_cards"):
    """
    Save each detected card as a separate PNG file

    Args:
        image: Original image (numpy array)
        detected_cards: Output from detect_cards()
        output_dir: Directory to save the card images
    """
    os.makedirs(output_dir, exist_ok=True)

    for i, card in enumerate(extracted_cards):
        filename = os.path.join(output_dir, f"table_card_{i + 1}.png")
        cv2.imwrite(filename, card)
        print(f"Saved: {filename}")


def save_readed_player_cards(results, output_dir="resources/readed_player_cards"):
    """Save each detected card region"""
    os.makedirs(output_dir, exist_ok=True)

    for i, detection in enumerate(results['detections']):
        card_region = detection['card_region']
        template_name = detection['template_name']
        confidence = detection['match_score']
        scale = detection['scale']

        filename = os.path.join(output_dir, f"{template_name}_conf{confidence:.2f}_scale{scale:.1f}_{i}.png")
        cv2.imwrite(filename, card_region)
        print(f"Saved: {filename}")

    return len(results['detections'])