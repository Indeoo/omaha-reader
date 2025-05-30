# ─── Helpers ─────────────────────────────────────────────────────────────────
import glob
import os

import cv2


def load_templates(template_dir):
    """Load all PNG templates as grayscale."""
    templates = {}
    for tpl_path in glob.glob(os.path.join(template_dir, '*.png')):
        name = os.path.basename(tpl_path).split('.')[0]  # e.g. "AS", "10H"
        tpl  = cv2.imread(tpl_path, cv2.IMREAD_COLOR)
        templates[name] = tpl
    return templates