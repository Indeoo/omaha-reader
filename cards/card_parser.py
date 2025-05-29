import cv2
import glob
import os
import numpy as np
from cards.template_loader import load_templates

# ─── Configuration ────────────────────────────────────────────────────────────
# Multiple HSV ranges to try (you may need to adjust these)
TABLE_HSV_RANGES = [
    # Original range
    ((36, 50, 50), (86, 255, 255)),
    # Wider green range
    ((25, 30, 30), (95, 255, 255)),
    # Dark green range
    ((40, 40, 40), (80, 255, 150)),
    # Very wide range
    ((20, 20, 20), (100, 255, 255))
]

# how much confidence is enough to accept a match
MATCH_CONFIDENCE = 0.90

# paths
BASE_DIR = os.path.dirname(__file__)
FULL_TEMPLATE_DIR = os.path.normpath(os.path.join(BASE_DIR, 'templates', 'full_cards'))
HANDS_TEMPLATE_DIR = os.path.normpath(os.path.join(BASE_DIR, 'templates', 'hand_cards'))
INPUT_DIR = os.path.normpath(os.path.join(BASE_DIR, 'screenshots'))
OUTPUT_DIR = os.path.normpath(os.path.join(BASE_DIR, 'output'))
DEBUG_DIR = os.path.normpath(os.path.join(BASE_DIR, 'debug'))


def analyze_image_colors(img, output_path=None):
    """
    Analyze the HSV color distribution in the image to help tune table detection.
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    print(f"HSV Analysis:")
    print(f"  Hue: min={h.min()}, max={h.max()}, mean={h.mean():.1f}")
    print(f"  Saturation: min={s.min()}, max={s.max()}, mean={s.mean():.1f}")
    print(f"  Value: min={v.min()}, max={v.max()}, mean={v.mean():.1f}")

    if output_path:
        # Save HSV channels for visual inspection
        cv2.imwrite(output_path.replace('.png', '_hue.png'), h)
        cv2.imwrite(output_path.replace('.png', '_sat.png'), s)
        cv2.imwrite(output_path.replace('.png', '_val.png'), v)


def verify_templates(templates):
    """
    Check template format and convert if necessary.
    """
    print("Template verification:")
    converted_templates = {}

    for name, tpl in templates.items():
        print(f"  {name}: shape={tpl.shape}, dtype={tpl.dtype}")

        # Convert to grayscale if needed
        if len(tpl.shape) == 3:
            tpl_gray = cv2.cvtColor(tpl, cv2.COLOR_BGR2GRAY)
            print(f"    Converted to grayscale: {tpl_gray.shape}")
        else:
            tpl_gray = tpl

        # Ensure uint8 dtype
        if tpl_gray.dtype != np.uint8:
            tpl_gray = tpl_gray.astype(np.uint8)
            print(f"    Converted to uint8")

        converted_templates[name] = tpl_gray

    return converted_templates


def find_card_boxes_multi_method(img, debug_path=None):
    """
    Try multiple methods to find card boxes and return the best result.
    """
    all_methods_boxes = []

    # Method 1: Original HSV masking with multiple ranges
    for i, (lower, upper) in enumerate(TABLE_HSV_RANGES):
        boxes = find_card_boxes_hsv(img, lower, upper)
        all_methods_boxes.append((f"HSV_Range_{i}", boxes))

        if debug_path:
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, lower, upper)
            inv = cv2.bitwise_not(mask)
            cv2.imwrite(debug_path.replace('.png', f'_hsv_mask_{i}.png'), mask)
            cv2.imwrite(debug_path.replace('.png', f'_hsv_inv_{i}.png'), inv)

    # Method 2: Edge detection approach
    boxes = find_card_boxes_edges(img)
    all_methods_boxes.append(("Edges", boxes))

    # Method 3: Adaptive threshold approach
    boxes = find_card_boxes_adaptive(img)
    all_methods_boxes.append(("Adaptive", boxes))

    # Print results from all methods
    for method_name, boxes in all_methods_boxes:
        print(f"  {method_name}: {len(boxes)} boxes")

    # Return the method with most reasonable number of boxes (between 2-10)
    valid_methods = [(name, boxes) for name, boxes in all_methods_boxes
                     if 2 <= len(boxes) <= 10]

    if valid_methods:
        # Choose method with most boxes (but reasonable count)
        best_method = max(valid_methods, key=lambda x: len(x[1]))
        print(f"  Selected method: {best_method[0]} with {len(best_method[1])} boxes")
        return best_method[1]
    else:
        # Fallback: return method with most boxes
        if all_methods_boxes:
            best_method = max(all_methods_boxes, key=lambda x: len(x[1]))
            print(f"  Fallback to: {best_method[0]} with {len(best_method[1])} boxes")
            return best_method[1]

    return []


def find_card_boxes_hsv(img, table_hsv_lower, table_hsv_upper):
    """
    Original HSV-based card detection method.
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, table_hsv_lower, table_hsv_upper)
    inv = cv2.bitwise_not(mask)

    # Add morphological operations to clean up the mask
    kernel = np.ones((3, 3), np.uint8)
    inv = cv2.morphologyEx(inv, cv2.MORPH_CLOSE, kernel)
    inv = cv2.morphologyEx(inv, cv2.MORPH_OPEN, kernel)

    cnts, _ = cv2.findContours(inv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        aspect = w / float(h)
        area = w * h

        # More flexible aspect ratio and area thresholds
        if 0.5 < aspect < 2.0 and area > 5000:
            boxes.append((x, y, w, h))

    return boxes


def find_card_boxes_edges(img):
    """
    Edge detection based approach.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Edge detection
    edges = cv2.Canny(blurred, 50, 150)

    # Dilate to connect nearby edges
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=2)

    cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        aspect = w / float(h)
        area = w * h

        if 0.5 < aspect < 2.0 and area > 5000:
            boxes.append((x, y, w, h))

    return boxes


def find_card_boxes_adaptive(img):
    """
    Adaptive thresholding approach.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply adaptive threshold
    adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY_INV, 11, 2)

    # Clean up with morphological operations
    kernel = np.ones((5, 5), np.uint8)
    adaptive = cv2.morphologyEx(adaptive, cv2.MORPH_CLOSE, kernel)
    adaptive = cv2.morphologyEx(adaptive, cv2.MORPH_OPEN, kernel)

    cnts, _ = cv2.findContours(adaptive, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        aspect = w / float(h)
        area = w * h

        if 0.5 < aspect < 2.0 and area > 5000:
            boxes.append((x, y, w, h))

    return boxes


def match_card(card_gray, templates):
    """
    Run template matching of a grayscale card image against all grayscale templates.
    Returns (best_name, best_score) or (None, 0).
    """
    best_score = 0.0
    best_name = None

    # Ensure card_gray is single channel grayscale
    if len(card_gray.shape) == 3:
        card_gray = cv2.cvtColor(card_gray, cv2.COLOR_BGR2GRAY)

    # Ensure consistent data type
    if card_gray.dtype != np.uint8:
        card_gray = card_gray.astype(np.uint8)

    print(f"    Card image shape: {card_gray.shape}, dtype: {card_gray.dtype}")

    for name, tpl in templates.items():
        # Ensure template is single channel grayscale
        if len(tpl.shape) == 3:
            tpl = cv2.cvtColor(tpl, cv2.COLOR_BGR2GRAY)

        # Ensure consistent data type
        if tpl.dtype != np.uint8:
            tpl = tpl.astype(np.uint8)

        # skip if template larger than card crop
        if tpl.shape[0] > card_gray.shape[0] or tpl.shape[1] > card_gray.shape[1]:
            continue

        try:
            res = cv2.matchTemplate(card_gray, tpl, cv2.TM_CCOEFF_NORMED)
            _, score, _, _ = cv2.minMaxLoc(res)

            if score > best_score:
                best_score, best_name = score, name
        except cv2.error as e:
            print(f"    Template matching error for {name}: {e}")
            print(f"    Card shape: {card_gray.shape}, Template shape: {tpl.shape}")
            print(f"    Card dtype: {card_gray.dtype}, Template dtype: {tpl.dtype}")
            continue

    return best_name, best_score


# ─── Main Routine ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(DEBUG_DIR, exist_ok=True)

    templates = load_templates(FULL_TEMPLATE_DIR)
    print(f"Loaded {len(templates)} templates")

    # Verify and convert templates to consistent format
    templates = verify_templates(templates)

    for infile in glob.glob(os.path.join(INPUT_DIR, '*.*')):
        print(f"\nProcessing: {infile}")
        img = cv2.imread(infile)

        if img is None:
            print(f"Could not load image: {infile}")
            continue

        print(f"Image dimensions: {img.shape}")

        # Debug: analyze colors in the image
        debug_base = os.path.join(DEBUG_DIR, os.path.splitext(os.path.basename(infile))[0])
        analyze_image_colors(img, debug_base + '_analysis.png')

        # Find card boxes using multiple methods
        print("Trying different detection methods:")
        boxes = find_card_boxes_multi_method(img, debug_base + '_debug.png')

        print(f"Final result: Found {len(boxes)} cards in {infile}")

        # Process detected cards
        for idx, (x, y, w, h) in enumerate(boxes, start=1):
            print(f"  Processing card {idx}: box=({x},{y},{w},{h})")
            crop = img[y:y + h, x:x + w]

            # Ensure we have a valid crop
            if crop.size == 0:
                print(f"    Empty crop, skipping card {idx}")
                continue

            # Convert to grayscale properly
            crop_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            print(f"    Crop shape: {crop.shape} -> {crop_gray.shape}, dtype: {crop_gray.dtype}")

            name, score = match_card(crop_gray, templates)
            if name and score >= MATCH_CONFIDENCE:
                label = f"{name} ({score:.2f})"
                color = (0, 255, 0)  # Green for confident matches
                print(f"    Confident match: {label}")
            else:
                label = f"Unknown ({score:.2f})" if name else "No match"
                color = (0, 0, 255)  # Red for uncertain matches
                print(f"    Low confidence: {label}")

            # annotate on original
            cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
            cv2.putText(img, label, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # save the individual crop
            safe_label = label.replace('/', '_').replace('\\', '_').replace('(', '').replace(')', '').replace(' ', '_')
            out_crop = os.path.join(
                OUTPUT_DIR,
                f"{os.path.splitext(os.path.basename(infile))[0]}_card{idx}_{safe_label}.png"
            )
            cv2.imwrite(out_crop, crop)
            print(f"    Saved crop: {out_crop}")

        # save annotated full image
        out_annot = os.path.join(
            OUTPUT_DIR,
            os.path.splitext(os.path.basename(infile))[0] + '_annotated.png'
        )
        cv2.imwrite(out_annot, img)

    print("\nDone processing all screenshots.")
    print(f"Check the '{DEBUG_DIR}' folder for debugging images.")
    print("Look at the HSV channel images to understand your table colors better.")