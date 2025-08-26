from typing import Dict, Tuple, List

import cv2
import numpy as np
import pytesseract
from loguru import logger

from shared.domain.detected_bid import DetectedBid

# Player position coordinates (position_id: (x, y, width, height))
PLAYER_BID_POSITIONS = {
    1: (390, 333, 40, 15),  # Bottom center (hero)
    2: (200, 310, 40, 15),  # Left side
    3: (200, 212, 45, 15),  # Top left
    4: (462, 165, 45, 15),  # Top center
    5: (578, 212, 30, 15),  # Top right
    6: (578, 310, 25, 15),  # Right side
}

BIDS_POSITIONS = {
    1: (388, 334, 45, 15),
    2: (200, 310, 40, 15),
    3: (185, 212, 45, 15),
    4: (450, 165, 45, 15),
    5: (572, 207, 40, 25),
    6: (562, 310, 45, 20),
}

# OCR configuration optimized for bid amounts
TESSERACT_CONFIG = (
    "--psm 7 --oem 3 "
    "-c tessedit_char_whitelist=0123456789. "
    "-c load_system_dawg=0 -c load_freq_dawg=0"
)


def detect_bids(cv2_image: np.ndarray, debug = False) -> Dict[int, DetectedBid]:
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

        # Visualize all processed regions on single plot
        if debug:
            import matplotlib.pyplot as plt
            fig, axes = plt.subplots(2, 3, figsize=(12, 8))
            axes = axes.ravel()
            for idx, (position, processed_region) in enumerate(processed_regions.items()):
                axes[idx].imshow(processed_region, cmap='gray')
                axes[idx].set_title(f'Position {position}')
            plt.tight_layout()
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
        # Get detailed OCR data with confidence scores and positions
        data = pytesseract.image_to_data(processed_region, config=TESSERACT_CONFIG, output_type=pytesseract.Output.DICT)

        # Filter for high-confidence text detections
        valid_texts = []
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            conf = int(data['conf'][i])

            # Only consider non-empty text with decent confidence
            if text and conf > 40:
                valid_texts.append({
                    'text': text,
                    'conf': conf,
                    'left': data['left'][i],
                    'top': data['top'][i],
                    'width': data['width'][i],
                    'height': data['height'][i]
                })

        if not valid_texts:
            return ""

        # Sort by confidence (highest first)
        valid_texts.sort(key=lambda x: x['conf'], reverse=True)

        # Try to combine separate detections into a single bid amount
        combined_text = _combine_bid_detections(valid_texts)

        return combined_text

    except Exception as e:
        logger.error(f"❌ Error extracting bid text at {bounds}: {str(e)}")
        return ""


def _combine_bid_detections(detections: List[Dict]) -> str:
    """Combine multiple OCR detections into a single bid amount"""
    if not detections:
        return ""

    # If only one detection, return it
    if len(detections) == 1:
        return detections[0]['text']

    # Try to find number + decimal point combinations
    numbers = []
    decimal_points = []

    for detection in detections:
        text = detection['text']
        if text.replace('.', '').isdigit():  # Contains only digits and maybe decimal
            numbers.append(detection)
        elif text == '.':
            decimal_points.append(detection)

    # If we have multiple numbers, try to combine them spatially
    if len(numbers) > 1:
        # Sort by horizontal position (left to right)
        numbers.sort(key=lambda x: x['left'])

        # Check if they're close enough horizontally to be part of same number
        combined = ""
        for i, num in enumerate(numbers):
            if i == 0:
                combined = num['text']
            else:
                # If close horizontally (within reasonable distance)
                prev_right = numbers[i - 1]['left'] + numbers[i - 1]['width']
                current_left = num['left']
                gap = current_left - prev_right

                if gap < 20:  # Adjust threshold based on your image scaling
                    # Check if there's a decimal point between them
                    decimal_between = any(
                        prev_right <= dp['left'] <= current_left
                        for dp in decimal_points
                    )

                    if decimal_between:
                        combined += "." + num['text']
                    else:
                        combined += num['text']
                else:
                    # Too far apart, probably separate numbers
                    break

        return combined

    # If we have one number and decimal points, try to construct full amount
    if len(numbers) == 1 and decimal_points:
        number_detection = numbers[0]
        # Find decimal point closest to the number
        closest_decimal = min(
            decimal_points,
            key=lambda dp: abs(dp['left'] - (number_detection['left'] + number_detection['width']))
        )

        # Check if decimal point is reasonably close
        distance = abs(closest_decimal['left'] - (number_detection['left'] + number_detection['width']))
        if distance < 15:  # Adjust threshold
            return number_detection['text'] + ".0"  # Assume .0 if no fractional part detected

    # Fallback: return the highest confidence detection
    return detections[0]['text']


def _preprocess_bid_region(region: np.ndarray, scale_factor = 8) -> np.ndarray:
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

    upscaled = cv2.resize(gray, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)

    # Binary threshold with inversion (text becomes white on black)
    # THRESH_BINARY_INV: Inverts the output so that text (which is usually darker) becomes white (255) on black (0) background
    # THRESH_OTSU: Automatically determines the optimal threshold value based on image histogram
    # This makes OCR more effective as it works better with white text on black background
    _, thresh = cv2.threshold(upscaled, 133, 255, cv2.THRESH_BINARY_INV)  # Start with 120

    return thresh


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
