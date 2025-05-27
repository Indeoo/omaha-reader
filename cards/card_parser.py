import cv2
import glob
import os
import numpy as np

# ─── Configuration ────────────────────────────────────────────────────────────
# threshold for table color (HSV) – adjust to your client theme
TABLE_HSV_LOWER = (36, 50, 50)
TABLE_HSV_UPPER = (86, 255, 255)

# how much confidence is enough to accept a match
MATCH_CONFIDENCE = 0.90

# paths
BASE_DIR     = os.path.dirname(__file__)
TEMPLATE_DIR = os.path.normpath(os.path.join(BASE_DIR, 'templates', 'full_cards'))
INPUT_DIR    = os.path.normpath(os.path.join(BASE_DIR, 'screenshots'))
OUTPUT_DIR   = os.path.normpath(os.path.join(BASE_DIR, 'output'))

# ─── Helpers ─────────────────────────────────────────────────────────────────
def load_templates(template_dir):
    """Load all PNG templates as grayscale."""
    templates = {}
    for tpl_path in glob.glob(os.path.join(template_dir, '*.png')):
        name = os.path.basename(tpl_path).split('.')[0]  # e.g. "AS", "10H"
        tpl  = cv2.imread(tpl_path, cv2.IMREAD_GRAYSCALE)
        templates[name] = tpl
    return templates

def find_card_boxes(img):
    """
    Mask out table color, invert, find contours,
    and return bounding boxes that look like cards.
    """
    hsv    = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask   = cv2.inRange(hsv, TABLE_HSV_LOWER, TABLE_HSV_UPPER)
    inv    = cv2.bitwise_not(mask)
    cnts,_ = cv2.findContours(inv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for c in cnts:
        x,y,w,h = cv2.boundingRect(c)
        aspect = w / float(h)
        area   = w * h
        if 0.6 < aspect < 1.6 and area > 15000:
            boxes.append((x,y,w,h))
    return boxes

def match_card(card_gray, templates):
    """
    Run template matching of a grayscale card image against all grayscale templates.
    Returns (best_name, best_score) or (None, 0).
    """
    best_score = 0.0
    best_name  = None
    for name, tpl in templates.items():
        # skip if template larger than card crop
        if tpl.shape[0] > card_gray.shape[0] or tpl.shape[1] > card_gray.shape[1]:
            continue
        res = cv2.matchTemplate(card_gray, tpl, cv2.TM_CCOEFF_NORMED)
        _, score, _, _ = cv2.minMaxLoc(res)
        if score > best_score:
            best_score, best_name = score, name
    return best_name, best_score

# ─── Main Routine ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    templates = load_templates(TEMPLATE_DIR)

    for infile in glob.glob(os.path.join(INPUT_DIR, '*.*')):
        img   = cv2.imread(infile)
        boxes = find_card_boxes(img)

        for idx, (x,y,w,h) in enumerate(boxes, start=1):
            crop      = img[y:y+h, x:x+w]
            crop_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

            name, score = match_card(crop_gray, templates)
            if name and score >= MATCH_CONFIDENCE:
                label = f"{name} ({score:.2f})"
            else:
                label = f"Unknown ({score:.2f})"

            # annotate on original
            cv2.rectangle(img, (x,y), (x+w,y+h), (0,255,0), 2)
            cv2.putText(img, label, (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

            # save the individual crop
            out_crop = os.path.join(
                OUTPUT_DIR,
                f"{os.path.splitext(os.path.basename(infile))[0]}_card{idx}_{label}.png"
            )
            cv2.imwrite(out_crop, crop)

        # save annotated full image
        out_annot = os.path.join(
            OUTPUT_DIR,
            os.path.splitext(os.path.basename(infile))[0] + '_annotated.png'
        )
        cv2.imwrite(out_annot, img)

    print("Done processing all screenshots.")
