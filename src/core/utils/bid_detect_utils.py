from typing import Dict, Tuple, Optional
import cv2
import pytesseract
import numpy as np
from loguru import logger

from src.core.domain.detected_bid import DetectedBid

# Player position coordinates (position_id: (x, y, width, height))
PLAYER_BID_POSITIONS = {
    1: (388, 334, 45, 15),  # Bottom center (hero)
    2: (200, 310, 40, 15),  # Left side
    3: (185, 212, 45, 15),  # Top left
    4: (450, 165, 45, 15),  # Top center
    5: (572, 207, 40, 25),  # Top right
    6: (562, 310, 45, 20),  # Right side
}

# OCR configuration optimized for bid amounts
TESSERACT_CONFIG = (
    "--psm 7 --oem 3 "
    "-c tessedit_char_whitelist=0123456789. "
    "-c load_system_dawg=0 -c load_freq_dawg=0"
)


def detect_bids(cv2_image: np.ndarray) -> Dict[int, DetectedBid]:
    """
    Detect bid amounts for all player positions

    Args:
        cv2_image: Full poker table screenshot

    Returns:
        Dictionary mapping position number to DetectedBid object
    """
    detected_bids = {}

    try:
        # First extract all regions
        processed_regions = {}
        for position, bounds in PLAYER_BID_POSITIONS.items():
            x, y, w, h = bounds
            region = cv2_image[y:y + h, x:x + w]
            processed_regions[position] = _preprocess_bid_region(region)

        # Visualize all processed regions
        for position, processed_region in processed_regions.items():
            import matplotlib.pyplot as plt
            plt.figure(figsize=(4, 4))
            plt.imshow(processed_region, cmap='gray')
            plt.title(f'Position {position}')
            plt.show()

        # Process each region for bids
        for position, processed_region in processed_regions.items():
            bounds = PLAYER_BID_POSITIONS[position]
            bid_text = _extract_bid_text(processed_region, bounds)

            if bid_text and _is_valid_bid_text(bid_text):
                detected_bid = _create_detected_bid(position, bid_text, bounds)
                detected_bids[position] = detected_bid
                logger.info(f"Position {position}: ${bid_text}")

        return detected_bids

    except Exception as e:
        logger.error(f"❌ Error detecting bids: {str(e)}")
        return {}


def _extract_bid_text(processed_region, bounds: Tuple[int, int, int, int]) -> str:
    """Extract bid text from specific image region using OCR"""
    try:
        # Extract text
        text = pytesseract.image_to_string(processed_region, config=TESSERACT_CONFIG).strip()

        return text

    except Exception as e:
        logger.error(f"❌ Error extracting bid text at {bounds}: {str(e)}")
        return ""


def _preprocess_bid_region(region: np.ndarray) -> np.ndarray:
    """
    Preprocess image region for optimal OCR performance

    Steps:
    1. Convert to grayscale
    2. Apply binary threshold with inversion (white text on black background):
       - This converts the grayscale image to a binary image where pixels are either 0 (black) or 255 (white)
       - The inversion (THRESH_BINARY_INV) makes text appear as white pixels on a black background
       - OTSU's method automatically determines the optimal threshold value based on the image histogram
       - This preprocessing step significantly improves OCR accuracy as most OCR engines work better with
         white text on black background
    3. Upscale 4x to make decimal points more visible
    4. Apply morphological dilation to connect small elements
    """
    # Convert to grayscale
    if len(region.shape) == 3:
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    else:
        gray = region.copy()

    # Binary threshold with inversion (text becomes white on black)
    # THRESH_BINARY_INV: Inverts the output so that text (which is usually darker) becomes white (255) on black (0) background
    # THRESH_OTSU: Automatically determines the optimal threshold value based on image histogram
    # This makes OCR more effective as it works better with white text on black background
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

    # Upscale for better decimal point recognition
    scale_factor = 2

    upscaled = cv2.resize(thresh, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)

    # Dilate to connect decimal points with numbers
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    dilated = cv2.dilate(upscaled, kernel, iterations=1)

    return dilated


def _is_valid_bid_text(text: str) -> bool:
    """Check if extracted text represents a valid bid amount"""
    if not text:
        return False

    # Remove any whitespace
    text = text.strip()

    # Check if text contains only digits and at most one decimal point
    if not text.replace('.', '').replace(',', '').isdigit():
        return False

    # Check decimal point count
    if text.count('.') > 1:
        return False

    # Try to convert to float to ensure it's a valid number
    try:
        amount = float(text)
        return amount >= 0
    except ValueError:
        return False


def _create_detected_bid(position: int, bid_text: str, bounds: Tuple[int, int, int, int]) -> DetectedBid:
    """Create DetectedBid object from extracted data"""
    x, y, w, h = bounds
    center = (x + w // 2, y + h // 2)

    return DetectedBid(
        position=position,
        amount_text=bid_text,
        bounding_rect=bounds,
        center=center
    )
