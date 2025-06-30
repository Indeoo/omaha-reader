import cv2
import pytesseract

from src.core.domain.captured_window import CapturedWindow


def detect_single_bid(captured_image: CapturedWindow, x: int, y: int, w: int, h: int) -> str:
    try:
        cv2_image = captured_image.get_cv2_image()
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
        print(f"❌ Error detecting bids at ({x}, {y}): {str(e)}")
        return ""