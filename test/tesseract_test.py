from PIL import Image, ImageEnhance, ImageOps
import pytesseract
import re


if __name__ == "__main__":
    # Load image
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

    #print(text_full.strip())

    total_match = re.search(r'Total.?pot[:\s]*([\d.]+)', text_full)
    main_match = re.search(r'Main.?pot[:\s]*([\d.]+)', text_full)

    total_pot = total_match.group(1) if total_match else "Not found"
    main_pot = main_match.group(1) if main_match else "Not found"

    print(total_pot)
    print(main_pot)