import cv2
import numpy as np

from cards.template_loader import load_templates


def extract_card(image, card_info):
    """Extract card region using perspective transform"""
    # Get rotated rectangle
    rect = card_info['rotated_rect']
    box = card_info['box_points']

    # Get dimensions
    width = int(rect[1][0])
    height = int(rect[1][1])

    # Ensure width > height for consistent orientation
    # # FORCE all cards to be vertical (height > width)
    # if width > height:
    #     width, height = height, width

    # Destination points for perspective transform
    dst_pts = np.array([
        [0, height - 1],
        [0, 0],
        [width - 1, 0],
        [width - 1, height - 1]
    ], dtype="float32")

    # Source points from detected card
    src_pts = box.astype("float32")

    # Get perspective transform matrix and apply
    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped = cv2.warpPerspective(image, M, (width, height))

    return warped


def match_card_to_templates(card_region, templates, threshold=0.6):
    """Match extracted card region to templates"""
    if not templates:
        return None, 0.0, False

    card_gray = cv2.cvtColor(card_region, cv2.COLOR_BGR2GRAY)
    h, w = card_gray.shape

    best_match = None
    best_score = 0.0

    for template_name, template in templates.items():
        # Resize template to match card
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        template_resized = cv2.resize(template_gray, (w, h))

        # Template matching
        result = cv2.matchTemplate(card_gray, template_resized, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)

        if max_val > best_score:
            best_score = max_val
            best_match = template_name

    is_valid = best_score >= threshold
    return best_match, best_score, is_valid


def validate_detected_cards(image, detected_cards, template_dir="templates/full_cards", threshold=0.6):
    """
    Validate detected cards against templates

    Args:
        image: Original image (numpy array)
        detected_cards: Output from your detect_cards() function
        template_dir: Directory containing template images
        threshold: Minimum match score (0.0-1.0)

    Returns:
        Dictionary with validation results
    """
    # Load templates
    templates = load_templates(template_dir)

    if not templates:
        return {"error": "No templates loaded"}

    results = {
        "table_cards": [],
        "summary": {"total": 0, "valid": 0, "invalid": 0}
    }

    # Validate table cards
    for i, card in enumerate(detected_cards['table_cards']):
        card_region = extract_card(image, card)
        match_name, score, is_valid = match_card_to_templates(card_region, templates, threshold)

        result = {
            "card_index": i,
            "match": match_name,
            "score": score,
            "is_valid": is_valid,
            "card_region": card_region
        }
        results["table_cards"].append(result)

        print(f"Table card {i + 1}: {match_name} (score: {score:.3f}) - {'✓' if is_valid else '✗'}")

    # Calculate summary
    total_cards = len(results["table_cards"])
    valid_cards = sum(1 for card in results["table_cards"] if card["is_valid"])

    results["summary"] = {
        "total": total_cards,
        "valid": valid_cards,
        "invalid": total_cards - valid_cards,
        "validation_rate": (valid_cards / total_cards * 100) if total_cards > 0 else 0
    }

    print(
        f"\nValidation Summary: {valid_cards}/{total_cards} cards valid ({results['summary']['validation_rate']:.1f}%)")

    return results