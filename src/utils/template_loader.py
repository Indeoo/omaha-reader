# ─── Helpers ─────────────────────────────────────────────────────────────────
import glob
import os

import cv2


def load_templates(template_dir):
    """Load all PNG templates as grayscale."""
    print(f"📁 Loading templates from: {template_dir}")

    templates = {}
    for tpl_path in glob.glob(os.path.join(template_dir, '*.png')):
        name = os.path.basename(tpl_path).split('.')[0]  # e.g. "AS", "10H"
        tpl  = cv2.imread(tpl_path, cv2.IMREAD_COLOR)
        templates[name] = tpl

    print(f"✅ Loaded {len(templates)} templates: {list(templates.keys())}")

    return templates


# def load_templates(template_dir):
#     templates = {}
#     for tpl_path in glob.glob(os.path.join(template_dir, '*.png')):
#         name = os.path.basename(tpl_path).split('.')[0]
#         tpl = cv2.imread(tpl_path, cv2.IMREAD_COLOR)
#
#         # Add template preprocessing
#         tpl = cv2.GaussianBlur(tpl, (1, 1), 0)  # Slight blur to reduce noise
#         tpl = cv2.convertScaleAbs(tpl, alpha=1.1, beta=10)  # Enhance contrast
#
#         templates[name] = tpl
#
#
#     print(f"✅ Loaded {len(templates)} templates: {list(templates.keys())}")
#
#     return templates


# def load_templates(template_dir):
#     templates = {}
#     for tpl_path in glob.glob(os.path.join(template_dir, '*.png')):
#         name = os.path.basename(tpl_path).split('.')[0]
#         # Load in color and also create HSV version for better suit distinction
#         tpl_bgr = cv2.imread(tpl_path, cv2.IMREAD_COLOR)
#         tpl_hsv = cv2.cvtColor(tpl_bgr, cv2.COLOR_BGR2HSV)
#         templates[name] = {'bgr': tpl_bgr, 'hsv': tpl_hsv}
#
#     print(f"✅ Loaded {len(templates)} templates: {list(templates.keys())}")
#
#     return templates