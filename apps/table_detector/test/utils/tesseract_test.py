import re
import unittest

import cv2
import pytesseract
from PIL import Image, ImageEnhance, ImageOps
from loguru import logger
from matplotlib import pyplot as plt


class TestPytesseract(unittest.TestCase):
    def testPot(self):
        img = Image.open(
            f"Dropbox/data_screenshots/_20250610_023049/_20250610_025342/02_unknown__2_50__5_Pot_Limit_Omaha.png")

        # # Load full image and preprocess
        gray_full = img.convert("L")
        enhanced_full = ImageEnhance.Contrast(gray_full).enhance(2.0)
        threshold_full = enhanced_full.point(lambda x: 0 if x < 128 else 255, '1')

        # Invert for better OCR performance
        inverted_full = ImageOps.invert(threshold_full.convert("L"))

        # Resize to 2x for better OCR
        resized_full = inverted_full.resize((inverted_full.width * 2, inverted_full.height * 2))

        # OCR with digit whitelist
        config = "--psm 6 -c tessedit_char_whitelist=0123456789.:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        text_full = pytesseract.image_to_string(resized_full, config=config)

        logger.info(text_full.strip())

        total_match = re.search(r'Total.?pot[:\s]*([\d.]+)', text_full)
        main_match = re.search(r'Main.?pot[:\s]*([\d.]+)', text_full)

        total_pot = total_match.group(1) if total_match else "Not found"
        main_pot = main_match.group(1) if main_match else "Not found"

        logger.info(total_pot)
        logger.info(main_pot)

    def testBalances(self):
        # Load and preprocess image
        img = cv2.imread(
            f"Dropbox/data_screenshots/_20250610_023049/_20250610_025342/02_unknown__2_50__5_Pot_Limit_Omaha.png")

        # Load full image and convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Invert for white-on-dark text
        inv = cv2.bitwise_not(gray)

        # Threshold to clean background
        _, thresh = cv2.threshold(inv, 160, 255, cv2.THRESH_BINARY)

        # Resize to boost OCR accuracy
        resized = cv2.resize(thresh, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)

        # OCR config: digits and dots only
        config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.'

        # Run OCR
        data = pytesseract.image_to_data(resized, config=config, output_type=pytesseract.Output.DICT)

        # Filter results with confidence and non-empty text
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            conf = int(data['conf'][i])
            if text != '' and conf > 80:
                logger.info(f"Text: {text} | Confidence: {conf} | Position: ({data['left'][i]}, {data['top'][i]})")

        seat_coords = {
            'CO': (370, 430, 90, 25),
            'BB': (420, 120, 70, 25),
            'SB': (150, 270, 80, 25),
        }

        for seat, (x, y, w, h) in seat_coords.items():
            crop = gray[y:y + h, x:x + w]
            crop = cv2.bitwise_not(crop)
            _, crop = cv2.threshold(crop, 160, 255, cv2.THRESH_BINARY)
            crop = cv2.resize(crop, None, fx=2, fy=2)
            text = pytesseract.image_to_string(crop, config=config)
            logger.info(f"{seat}: {text.strip()}")

        # for i in range(len(data['text'])):
        #     text = data['text'][i].strip()
        #     conf = int(data['conf'][i])
        #     if text != '' and conf > 80:
        #         (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
        #         cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 1)
        #         cv2.putText(img, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        #
        # cv2.imshow("Detected Balances", img)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

    def testReadBid(self):
        # Load and preprocess image
        img_path = f"src/test/tables/test_move/4_move.png"
        # img = cv2.imread(f"Dropbox/data_screenshots/_20250610_023049/_20250610_025342/02_unknown__2_50__5_Pot_Limit_Omaha.png")

        img = cv2.imread(img_path)
        # Convert BGR to RGB for display
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Print image shape for reference
        logger.info("Image shape (h, w, c):", img.shape)

        # Initial guess for bubble ROI (tweak these values as needed)
        x, y, w, h = 200, 310, 40, 15
        roi = img_rgb[y:y + h, x:x + w]

        # Draw rectangle on the original image for context
        img_with_rect = img_rgb.copy()
        cv2.rectangle(img_with_rect, (x, y), (x + w, y + h), (255, 0, 0), 2)

        # Display the original with rectangle and the cropped ROI
        fig, axes = plt.subplots(1, 2, figsize=(10, 5))
        axes[0].imshow(img_with_rect)
        axes[0].set_title("Original with ROI")
        axes[0].axis("off")

        axes[1].imshow(roi)
        axes[1].set_title("Cropped Bubble")
        axes[1].axis("off")

        plt.show()

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        crop = gray[y:y + h, x:x + w]

        # 3. Binarize (invert so text is white on black)
        _, thresh = cv2.threshold(crop, 0, 255,
                                  cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

        # 4. Upscale so the decimal dot is larger
        upscaled = cv2.resize(thresh, None, fx=4, fy=4,
                              interpolation=cv2.INTER_CUBIC)

        # 5. Dilate to join tiny blobs (the “.”) into the text
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        dilated = cv2.dilate(upscaled, kernel, iterations=1)

        # 6. OCR with whitelist “0123456789.” and disable dictionaries
        config = (
            "--psm 7 --oem 3 "
            "-c tessedit_char_whitelist=0123456789. "
            "-c load_system_dawg=0 -c load_freq_dawg=0"
        )
        text = pytesseract.image_to_string(dilated, config=config).strip()

        logger.info("Detected bid:", text)

        # Map of coordinates for each position
        position_coords = {
            'POSITION6': (562, 310, 45, 20),
            'POSITION5': (572, 207, 40, 25),
            'POSITION4': (450, 165, 45, 15),
            'POSITION3': (185, 212, 45, 15),
            'POSITION2': (200, 310, 40, 15),  # 215 + 95
            'POSITION1': (386, 334, 45, 15)  # 214 + 120
        }
