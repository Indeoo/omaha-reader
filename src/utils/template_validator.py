import cv2
import numpy as np
from typing import Dict
from src.utils.template_loader import load_templates


def extract_card(image: np.ndarray, card_info: Dict, force_vertical: bool = True) -> np.ndarray:
    """
    Extract and straighten a card region using perspective transform.

    Args:
        image: Source image
        card_info: Card detection info with 'rotated_rect' and 'box_points'
        force_vertical: If True, ensure height > width for template matching

    Returns:
        Extracted card image
    """
    # Get rotated rectangle and box points
    rect = card_info['rotated_rect']
    box = card_info['box_points']

    # Get dimensions
    width = int(rect[1][0])
    height = int(rect[1][1])

    # Force vertical orientation if needed (for template matching)
    if force_vertical and width > height:
        width, height = height, width

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


def validate_detected_cards(image, detected_cards, template_dir, threshold=0.6):
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
    print(f"🔍 Starting validation with threshold: {threshold}")
    print(f"📁 Loading templates from: {template_dir}")

    # Load templates
    templates = load_templates(template_dir)

    if not templates:
        print(f"❌ No templates loaded from {template_dir}")
        return {"error": "No templates loaded"}

    print(f"✅ Loaded {len(templates)} templates: {list(templates.keys())}")

    results = {
        "table_cards": [],
        "summary": {"total": 0, "valid": 0, "invalid": 0}
    }

    valid_matches = []
    invalid_matches = []

    # Validate table cards
    print(f"🎯 Validating {len(detected_cards['table_cards'])} detected cards...")

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

        # Detailed logging for each card
        status = "✓ VALID" if is_valid else "✗ INVALID"
        print(f"Card {i + 1:2d}: {match_name or 'NO_MATCH':>8s} | Score: {score:.3f} | {status}")

        # Collect results for summary
        if is_valid:
            valid_matches.append(f"{match_name} ({score:.3f})")
        else:
            invalid_matches.append(f"{match_name or 'NO_MATCH'} ({score:.3f})")

    # Calculate summary
    total_cards = len(results["table_cards"])
    valid_cards = sum(1 for card in results["table_cards"] if card["is_valid"])

    results["summary"] = {
        "total": total_cards,
        "valid": valid_cards,
        "invalid": total_cards - valid_cards,
        "validation_rate": (valid_cards / total_cards * 100) if total_cards > 0 else 0
    }

    # Enhanced summary logging
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Total cards detected: {total_cards}")
    print(f"Valid cards: {valid_cards}")
    print(f"Invalid cards: {total_cards - valid_cards}")
    print(f"Validation rate: {results['summary']['validation_rate']:.1f}%")

    if valid_matches:
        print(f"\n✅ VALID CARDS ({len(valid_matches)}):")
        for i, match in enumerate(valid_matches, 1):
            print(f"  {i:2d}. {match}")

    if invalid_matches:
        print(f"\n❌ INVALID CARDS ({len(invalid_matches)}):")
        for i, match in enumerate(invalid_matches, 1):
            print(f"  {i:2d}. {match}")

    if not valid_matches and not invalid_matches:
        print("⚠️  No cards were processed!")

    print("=" * 60)

    return results


def log_card_distribution(results: Dict) -> None:
    """
    Log the distribution of detected card types
    """
    if not results.get("table_cards"):
        print("⚠️  No cards to analyze for distribution")
        return

    # Count card types
    card_counts = {}
    for card in results["table_cards"]:
        if card["is_valid"] and card["match"]:
            card_name = card["match"]
            card_counts[card_name] = card_counts.get(card_name, 0) + 1

    if card_counts:
        print("\n📊 CARD DISTRIBUTION:")
        for card_name, count in sorted(card_counts.items()):
            print(f"  {card_name}: {count} card{'s' if count > 1 else ''}")
    else:
        print("⚠️  No valid cards found for distribution analysis")


def log_validation_details(results: Dict, show_scores: bool = True) -> None:
    """
    Log detailed validation information
    """
    if not results.get("table_cards"):
        return

    print("\n🔍 DETAILED VALIDATION RESULTS:")
    print("-" * 50)

    for card in results["table_cards"]:
        idx = card["card_index"]
        match = card["match"] or "NO_MATCH"
        score = card["score"]
        status = "VALID" if card["is_valid"] else "INVALID"

        if show_scores:
            print(f"Card {idx + 1}: {match:>10s} | {score:.4f} | {status}")
        else:
            print(f"Card {idx + 1}: {match:>10s} | {status}")
