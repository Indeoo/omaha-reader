import glob
import os
from typing import List, Dict, Tuple

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



def draw_detected_cards(
        image: np.ndarray,
        detections: List[Dict],
        color: Tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2,
        font_scale: float = 0.6,
        show_scale: bool = True
) -> np.ndarray:
    """
    Draw detected cards on the image

    Args:
        image: Input image
        detections: List of detection dictionaries
        color: BGR color for drawing
        thickness: Line thickness
        font_scale: Font scale for labels
        show_scale: Whether to show scale information

    Returns:
        Image with drawn detections
    """
    result = image.copy()

    for i, detection in enumerate(detections):
        x, y, w, h = detection['bounding_rect']

        # Draw bounding rectangle
        cv2.rectangle(result, (x, y), (x + w, y + h), color, thickness)

        # Draw center point
        cv2.circle(result, detection['center'], 5, (255, 0, 0), -1)

        # Add label with template name and confidence
        label = f"{detection['template_name']} ({detection['match_score']:.2f})"
        cv2.putText(result, label, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)

        # Add scale info if requested
        if show_scale and 'scale' in detection:
            scale_info = f"Scale: {detection['scale']:.1f}"
            cv2.putText(result, scale_info, (x, y + h + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale * 0.7, (255, 255, 0), 1)

    return result


def draw_detected_positions(image, positions):
    """
    Draw detected positions on the image

    Args:
        image: OpenCV image
        positions: List of DetectedPosition objects

    Returns:
        Image with drawn positions
    """
    result = image.copy()

    for pos in positions:
        x, y, w, h = pos.bounding_rect

        # Draw bounding rectangle in yellow
        cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 255), 2)

        # Draw center point in red
        cv2.circle(result, pos.center, 5, (0, 0, 255), -1)

        # Add label with position name and confidence
        label = f"{pos.position_name} ({pos.match_score:.2f})"
        cv2.putText(result, label, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    return result


def coords_to_search_region(x: int, y: int, w: int, h: int,
                            image_width: int, image_height: int) -> tuple[float, float, float, float]:
    """
    Convert pixel coordinates to search region ratios.

    Args:
        x: Left coordinate of the region
        y: Top coordinate of the region
        w: Width of the region
        h: Height of the region
        image_width: Total image width
        image_height: Total image height

    Returns:
        Tuple of (left, top, right, bottom) as ratios (0.0 to 1.0)
    """
    left = x / image_width
    top = y / image_height
    right = (x + w) / image_width
    bottom = (y + h) / image_height

    # Clamp values between 0 and 1
    left = max(0.0, min(1.0, left))
    top = max(0.0, min(1.0, top))
    right = max(0.0, min(1.0, right))
    bottom = max(0.0, min(1.0, bottom))

    return (left, top, right, bottom)