from typing import Dict

import cv2
import pytesseract
from loguru import logger


BIDS_POSITIONS = {
        1: (388, 334, 45, 15),
        2: (200, 310, 40, 15),
        3: (185, 212, 45, 15),
        4: (450, 165, 45, 15),
        5: (572, 207, 40, 25),
        6: (562, 310, 45, 20),
    }


def detect_bids(cv2_image) -> Dict[int, float]:
    bids = {}

    try:
        logger.info(f"    <UNK> Found bids: {bids}")

        for position_name, (x, y, w, h) in BIDS_POSITIONS.items():
            bid = detect_single_bid(cv2_image, x, y, w, h)
            if bid:
                bids[position_name] = bid

        for position_name, bid_value in bids.items():
            logger.info(f"Position {position_name}: {bid_value}")

        return bids

    except Exception as e:
        logger.error(f"❌ Error detecting bids: {str(e)}")
        return {}


def detect_single_bid(cv2_image, x: int, y: int, w: int, h: int) -> str:
    try:
        gray = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2GRAY)

        crop = gray[y: y + h, x: x + w]

        _, thresh = cv2.threshold(
            crop, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU
        )

        upscaled = cv2.resize(
            thresh, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC
        )

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        dilated = cv2.dilate(upscaled, kernel, iterations=1)

        config = (
            "--psm 7 --oem 3 "
            "-c tessedit_char_whitelist=0123456789. "
            "-c load_system_dawg=0 -c load_freq_dawg=0"
        )
        text = pytesseract.image_to_string(dilated, config=config).strip()

        return text

    except Exception as e:
        logger.error(f"❌ Error detecting bids at ({x}, {y}): {str(e)}")
        return ""