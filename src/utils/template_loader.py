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

    if not templates:
        raise Exception("❌ No player templates loaded! Please check the templates directory.")
    else:
        print(f"✅ Loaded {len(templates)} templates: {list(templates.keys())}")

    return templates
