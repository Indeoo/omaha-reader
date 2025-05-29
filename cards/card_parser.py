import cv2
import glob
import os
import numpy as np
from cards.template_loader import load_templates

# ─── Configuration ────────────────────────────────────────────────────────────
MATCH_CONFIDENCE = 0.70

# Paths
BASE_DIR = os.path.dirname(__file__)
FULL_TEMPLATE_DIR = os.path.normpath(os.path.join(BASE_DIR, 'templates', 'full_cards'))
INPUT_DIR = os.path.normpath(os.path.join(BASE_DIR, 'screenshots'))
OUTPUT_DIR = os.path.normpath(os.path.join(BASE_DIR, 'output'))
DEBUG_DIR = os.path.normpath(os.path.join(BASE_DIR, 'debug'))


def find_colored_cards(img):
    """
    Detect poker cards by finding solid colored rectangular regions.
    Looking for: BLACK, GREEN, RED, BLUE backgrounds with white text.
    """
    print("=== COLORED CARD DETECTION ===")

    # Convert to HSV for better color detection
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    # Define color ranges for card backgrounds
    color_ranges = [
        # Format: (lower_hsv, upper_hsv, color_name)
        ((0, 0, 0), (180, 255, 80), "Black"),  # Black cards (low value)
        ((40, 50, 50), (80, 255, 255), "Green"),  # Green cards
        ((0, 50, 50), (10, 255, 255), "Red_1"),  # Red cards (lower range)
        ((170, 50, 50), (180, 255, 255), "Red_2"),  # Red cards (upper range)
        ((100, 50, 50), (130, 255, 255), "Blue"),  # Blue cards
    ]

    all_boxes = []

    for lower, upper, color_name in color_ranges:
        print(f"\nLooking for {color_name} cards...")

        # Create mask for this color range
        mask = cv2.inRange(hsv, lower, upper)

        # Clean up the mask
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)  # Remove noise
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)  # Fill gaps

        # Save debug mask
        debug_path = os.path.join(DEBUG_DIR, f"mask_{color_name.lower()}.png")
        cv2.imwrite(debug_path, mask)

        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for i, contour in enumerate(contours):
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            aspect_ratio = w / h

            print(f"  {color_name} contour {i}: ({x},{y}) {w}x{h}, area={area}, aspect={aspect_ratio:.2f}")

            # Card criteria based on your examples
            if (1000 < area < 25000 and  # Card-sized area
                    0.8 < aspect_ratio < 2.2 and  # Rectangular shape
                    w > 50 and h > 60 and  # Minimum dimensions
                    w < 250 and h < 350):  # Maximum dimensions

                print(f"    ✓ ACCEPTED as {color_name} card")
                all_boxes.append((x, y, w, h, color_name))
            else:
                print(f"    ✗ REJECTED")

    # Remove color info for return, just keep boxes
    return [(x, y, w, h) for x, y, w, h, _ in all_boxes]


def find_saturated_regions(img):
    """
    Alternative: Find regions with high saturation (colored cards vs neutral background)
    """
    print("\n=== SATURATED REGION DETECTION ===")

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    # Look for regions with high saturation (colored cards)
    _, sat_mask = cv2.threshold(s, 100, 255, cv2.THRESH_BINARY)

    # Also consider regions with medium saturation but good contrast
    _, sat_mask2 = cv2.threshold(s, 50, 255, cv2.THRESH_BINARY)
    _, val_mask = cv2.threshold(v, 80, 255, cv2.THRESH_BINARY)
    combined_mask = cv2.bitwise_and(sat_mask2, val_mask)

    # Combine both approaches
    final_mask = cv2.bitwise_or(sat_mask, combined_mask)

    # Clean up
    kernel = np.ones((5, 5), np.uint8)
    final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_CLOSE, kernel)
    final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_OPEN, kernel)

    # Save debug
    cv2.imwrite(os.path.join(DEBUG_DIR, "saturation_mask.png"), final_mask)

    contours, _ = cv2.findContours(final_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for i, contour in enumerate(contours):
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        aspect_ratio = w / h

        print(f"  Saturated contour {i}: ({x},{y}) {w}x{h}, area={area}, aspect={aspect_ratio:.2f}")

        if (1000 < area < 25000 and
                0.8 < aspect_ratio < 2.2 and
                w > 50 and h > 60 and
                w < 250 and h < 350):

            print(f"    ✓ ACCEPTED as colored region")
            boxes.append((x, y, w, h))
        else:
            print(f"    ✗ REJECTED")

    return boxes


def find_contrast_edges(img):
    """
    Find rectangular regions with strong internal contrast (colored background + white text)
    """
    print("\n=== CONTRAST EDGE DETECTION ===")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply strong Gaussian blur then find edges
    # This helps find regions with internal contrast (text on colored background)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(blurred, 50, 150)

    # Dilate to connect text edges within cards
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)

    # Close gaps to form solid regions
    kernel_large = np.ones((7, 7), np.uint8)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel_large)

    # Save debug
    cv2.imwrite(os.path.join(DEBUG_DIR, "contrast_edges.png"), edges)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for i, contour in enumerate(contours):
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        aspect_ratio = w / h

        print(f"  Edge contour {i}: ({x},{y}) {w}x{h}, area={area}, aspect={aspect_ratio:.2f}")

        if (1000 < area < 25000 and
                0.8 < aspect_ratio < 2.2 and
                w > 50 and h > 60 and
                w < 250 and h < 350):

            print(f"    ✓ ACCEPTED as contrast region")
            boxes.append((x, y, w, h))
        else:
            print(f"    ✗ REJECTED")

    return boxes


def remove_duplicate_boxes(boxes, overlap_threshold=0.3):
    """Remove overlapping boxes"""
    if len(boxes) <= 1:
        return boxes

    # Sort by area (largest first)
    boxes_with_area = [(x, y, w, h, w * h) for x, y, w, h in boxes]
    boxes_with_area.sort(key=lambda x: x[4], reverse=True)

    filtered_boxes = []

    for x1, y1, w1, h1, area1 in boxes_with_area:
        overlap_found = False

        for x2, y2, w2, h2 in filtered_boxes:
            # Calculate intersection over union
            xi1, yi1 = max(x1, x2), max(y1, y2)
            xi2, yi2 = min(x1 + w1, x2 + w2), min(y1 + h1, y2 + h2)

            if xi1 < xi2 and yi1 < yi2:
                intersection = (xi2 - xi1) * (yi2 - yi1)
                union = area1 + w2 * h2 - intersection
                iou = intersection / union if union > 0 else 0

                if iou > overlap_threshold:
                    overlap_found = True
                    break

        if not overlap_found:
            filtered_boxes.append((x1, y1, w1, h1))

    return filtered_boxes


def find_poker_cards_corrected(img):
    """
    Main detection function for COLORED cards with white text
    """
    print(f"Image shape: {img.shape}")

    # Try all three methods for colored cards
    colored_boxes = find_colored_cards(img)
    saturated_boxes = find_saturated_regions(img)
    contrast_boxes = find_contrast_edges(img)

    print(f"\nMethod results:")
    print(f"  Colored detection: {len(colored_boxes)} cards")
    print(f"  Saturated detection: {len(saturated_boxes)} cards")
    print(f"  Contrast detection: {len(contrast_boxes)} cards")

    # Combine all methods
    all_boxes = colored_boxes + saturated_boxes + contrast_boxes
    unique_boxes = remove_duplicate_boxes(all_boxes)

    print(f"  Combined unique: {len(unique_boxes)} cards")

    return unique_boxes


def prepare_templates(templates):
    """Convert templates to grayscale"""
    processed_templates = {}

    for name, template in templates.items():
        if len(template.shape) == 3:
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        else:
            template_gray = template

        if template_gray.dtype != np.uint8:
            template_gray = template_gray.astype(np.uint8)

        processed_templates[name] = template_gray

    return processed_templates


def match_card_improved(card_crop, templates):
    """Improved template matching"""
    # Convert to grayscale
    if len(card_crop.shape) == 3:
        card_gray = cv2.cvtColor(card_crop, cv2.COLOR_BGR2GRAY)
    else:
        card_gray = card_crop

    best_match = None
    best_score = 0

    # Try multiple scales
    scales = [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3]

    for scale in scales:
        if scale != 1.0:
            new_width = int(card_gray.shape[1] * scale)
            new_height = int(card_gray.shape[0] * scale)
            if new_width > 0 and new_height > 0:
                scaled_card = cv2.resize(card_gray, (new_width, new_height))
            else:
                continue
        else:
            scaled_card = card_gray

        for name, template in templates.items():
            if (template.shape[0] > scaled_card.shape[0] or
                    template.shape[1] > scaled_card.shape[1]):
                continue

            try:
                result = cv2.matchTemplate(scaled_card, template, cv2.TM_CCOEFF_NORMED)
                _, score, _, _ = cv2.minMaxLoc(result)

                if score > best_score:
                    best_score = score
                    best_match = name

            except cv2.error:
                continue

    return best_match, best_score


def save_detection_results(img, boxes, output_path):
    """Save image with detected cards outlined"""
    result_img = img.copy()

    for i, (x, y, w, h) in enumerate(boxes):
        cv2.rectangle(result_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(result_img, f"Card {i + 1}", (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv2.imwrite(output_path, result_img)
    print(f"Saved detection result: {output_path}")


def save_individual_cards(img, boxes, output_dir, base_name):
    """Save each detected card as individual image"""
    os.makedirs(output_dir, exist_ok=True)

    for i, (x, y, w, h) in enumerate(boxes):
        card_crop = img[y:y + h, x:x + w]
        card_path = os.path.join(output_dir, f"{base_name}_card_{i + 1}.png")
        cv2.imwrite(card_path, card_crop)
        print(f"Saved card {i + 1}: {card_path}")


# ─── Main Routine ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(DEBUG_DIR, exist_ok=True)

    print("Loading templates...")
    templates = load_templates(FULL_TEMPLATE_DIR)
    templates = prepare_templates(templates)
    print(f"Loaded {len(templates)} templates")

    for input_file in glob.glob(os.path.join(INPUT_DIR, '*.*')):
        print(f"\n{'=' * 60}")
        print(f"Processing: {input_file}")
        print(f"{'=' * 60}")

        img = cv2.imread(input_file)
        if img is None:
            continue

        base_name = os.path.splitext(os.path.basename(input_file))[0]

        # Detect COLORED cards
        detected_boxes = find_poker_cards_corrected(img)

        print(f"\n🎯 FINAL RESULT: Found {len(detected_boxes)} colored cards")
        for i, (x, y, w, h) in enumerate(detected_boxes):
            print(f"  Card {i + 1}: ({x},{y}) {w}x{h}")

        # Save results
        detection_result_path = os.path.join(OUTPUT_DIR, f"{base_name}_detected_colored_cards.png")
        save_detection_results(img, detected_boxes, detection_result_path)

        cards_dir = os.path.join(OUTPUT_DIR, f"{base_name}_colored_cards")
        save_individual_cards(img, detected_boxes, cards_dir, base_name)

        # Match cards
        if detected_boxes:
            print(f"\n🃏 CARD MATCHING:")
            result_img = img.copy()

            for i, (x, y, w, h) in enumerate(detected_boxes):
                card_crop = img[y:y + h, x:x + w]
                card_name, confidence = match_card_improved(card_crop, templates)

                if card_name and confidence >= MATCH_CONFIDENCE:
                    label = f"{card_name} ({confidence:.2f})"
                    color = (0, 255, 0)
                    print(f"  Card {i + 1}: {label} ✓")
                else:
                    label = f"Unknown ({confidence:.2f})" if card_name else "No match"
                    color = (0, 0, 255)
                    print(f"  Card {i + 1}: {label} ✗")

                cv2.rectangle(result_img, (x, y), (x + w, y + h), color, 2)
                cv2.putText(result_img, label, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            final_result_path = os.path.join(OUTPUT_DIR, f"{base_name}_colored_cards_result.png")
            cv2.imwrite(final_result_path, result_img)
            print(f"Saved final result: {final_result_path}")

    print(f"\n🎉 Processing complete!")