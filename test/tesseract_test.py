import unittest

import cv2
from PIL import Image, ImageEnhance, ImageOps
import pytesseract
import re


class TestPytesseract(unittest.TestCase):
    def testPot(self):
        img = Image.open(f"_20250610_023049/_20250610_025342/02_unknown__2_50__5_Pot_Limit_Omaha.png")

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

        print(text_full.strip())

        total_match = re.search(r'Total.?pot[:\s]*([\d.]+)', text_full)
        main_match = re.search(r'Main.?pot[:\s]*([\d.]+)', text_full)

        total_pot = total_match.group(1) if total_match else "Not found"
        main_pot = main_match.group(1) if main_match else "Not found"

        print(total_pot)
        print(main_pot)


    def testBalances(self):
        # Load and preprocess image
        img = cv2.imread(f"_20250610_023049/_20250610_025342/02_unknown__2_50__5_Pot_Limit_Omaha.png")


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
                print(f"Text: {text} | Confidence: {conf} | Position: ({data['left'][i]}, {data['top'][i]})")

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
            print(f"{seat}: {text.strip()}")

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


