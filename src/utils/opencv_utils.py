import glob
import os

import cv2
import numpy as np
from PIL import Image


def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
    """Convert PIL Image to OpenCV format"""
    # Warn if alpha channel will be lost
    if pil_image.mode in ('RGBA', 'LA'):
        print(f"Warning: Alpha channel in {pil_image.mode} image will be removed")

    # Convert PIL image to RGB if it's not already
    if pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')

    # Convert to numpy array and then to BGR for OpenCV
    cv2_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    return cv2_image


def save_opencv_image(image, folder_path, filename):
    """
    Save OpenCV image to specified folder

    Args:
        image: OpenCV image (numpy array)
        folder_path: Path to the folder where image should be saved
        filename: Name of the file (including extension)
    """
    os.makedirs(folder_path, exist_ok=True)
    filepath = os.path.join(folder_path, filename)
    cv2.imwrite(filepath, image)


def match_cv2_template(scaled_h, scaled_w, search_image, template):
    scaled_template = cv2.resize(template, (scaled_w, scaled_h))
    result = cv2.matchTemplate(search_image, scaled_template, cv2.TM_CCORR_NORMED)
    return result


def load_templates(template_dir):
    """Load all PNG templates as grayscale."""
    print(f"📁 Loading templates from: {template_dir}")

    templates = {}
    for tpl_path in glob.glob(os.path.join(template_dir, '*.png')):
        name = os.path.basename(tpl_path).split('.')[0]  # e.g. "AS", "10H"
        tpl  = read_cv2_image(tpl_path)
        templates[name] = tpl

    if not templates:
        raise Exception("❌ No player templates loaded! Please check the templates directory.")
    else:
        print(f"✅ Loaded {len(templates)} templates: {list(templates.keys())}")

    return templates


def read_cv2_image(tpl_path):
    return cv2.imread(tpl_path, cv2.IMREAD_COLOR)
