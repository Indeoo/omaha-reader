import cv2
import numpy as np
from typing import Dict


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

    # Determine if we need to rotate based on current orientation
    needs_rotation = force_vertical and width > height

    if needs_rotation:
        # Swap dimensions for vertical orientation
        target_width, target_height = height, width
    else:
        target_width, target_height = width, height

    # Destination points for perspective transform
    dst_pts = np.array([
        [0, target_height - 1],
        [0, 0],
        [target_width - 1, 0],
        [target_width - 1, target_height - 1]
    ], dtype="float32")

    # Source points from detected card
    src_pts = box.astype("float32")

    # If we need rotation, we need to reorder the source points
    # to match the desired orientation
    if needs_rotation:
        # Reorder points to achieve 90-degree counter-clockwise rotation
        # This rotates the mapping so the card appears upright
        src_pts = np.array([
            src_pts[3],  # Move point 3 to position 0
            src_pts[0],  # Move point 0 to position 1
            src_pts[1],  # Move point 1 to position 2
            src_pts[2]  # Move point 2 to position 3
        ], dtype="float32")

    # Get perspective transform matrix and apply
    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped = cv2.warpPerspective(image, M, (target_width, target_height))

    return warped


def match_card_to_templates(card_region, templates, threshold=0.6):
    """
    Match extracted card region to templates - always finds the BEST match
    instead of the first match above threshold
    """
    if not templates:
        return None, 0.0, False

    card_gray = cv2.cvtColor(card_region, cv2.COLOR_BGR2GRAY)
    h, w = card_gray.shape

    best_match = None
    best_score = 0.0
    all_scores = []  # Track all scores for analysis

    for template_name, template in templates.items():
        # Resize template to match card
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        template_resized = cv2.resize(template_gray, (w, h))

        # Template matching
        result = cv2.matchTemplate(card_gray, template_resized, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)

        # Store this score
        all_scores.append((template_name, max_val))

        # Update best match regardless of threshold
        if max_val > best_score:
            best_score = max_val
            best_match = template_name

    # Sort all scores to find second best for confidence analysis
    all_scores.sort(key=lambda x: x[1], reverse=True)
    second_best_score = all_scores[1][1] if len(all_scores) > 1 else 0.0

    # Enhanced validation: consider confidence gap
    confidence_gap = best_score - second_best_score

    # Original threshold check + confidence gap analysis
    if best_score >= threshold:
        if confidence_gap >= 0.1:  # High confidence - big gap between best and second
            is_valid = True
        elif confidence_gap >= 0.05:  # Medium confidence - require slightly higher score
            is_valid = best_score >= threshold + 0.05
        else:  # Low confidence - very close scores, require higher threshold
            is_valid = best_score >= threshold + 0.15
    else:
        is_valid = False

    return best_match, best_score, is_valid


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
