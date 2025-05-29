# This is a sample Python script.
import numpy as np
import pytesseract
from PIL import Image, ImageFilter
import os
import cv2


def extract_text_from_screenshot(image_path):
    # Load image using OpenCV
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Resize (upscale to improve OCR on small icons)
    gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_LINEAR)

    # Threshold to sharpen text
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Optional: sharpen filter
    thresh = cv2.GaussianBlur(thresh, (3, 3), 0)

    # Convert to PIL
    pil_img = Image.fromarray(thresh)

    # --- OCR Configuration ---
    # Unicode suits: ♠♥♦♣ = \u2660\u2665\u2666\u2663
    config = r'-l eng --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789♠♥♦♣'

    # Extract text
    text = pytesseract.image_to_string(pil_img, config=config)

    return text


def process_screenshots_folder(folder_path):
    results = {}
    # Create results directory if it doesn't exist
    os.makedirs('results', exist_ok=True)
    folder_images = get_folder_images(folder_path)
    print("Folder images got")

    # Then process images for each folder
    for folder_name, images in folder_images.items():
        results[folder_name] = {}
        folder_results_path = os.path.join('results', folder_name)
        os.makedirs(folder_results_path, exist_ok=True)
        for filename, image_path in images:
            text = extract_text_from_screenshot(image_path)
            print(f"Extracted {image_path}")
            results[folder_name][filename] = text
            results_file = os.path.join(folder_results_path, f'{filename}.txt')
            with open(results_file, 'w', encoding='utf-8') as f:
                f.write(f'Text extracted from {filename}:\n')
                f.write(f'{text}\n')

    return results


def get_folder_images(folder_path):
    folder_images = {}
    # First collect all image files
    for folder_name in os.listdir(folder_path):
        folder_full_path = os.path.join(folder_path, folder_name)

        if os.path.isdir(folder_full_path):
            images = []
            for filename in os.listdir(folder_full_path):
                if filename.endswith(('.png', '.jpg', '.jpeg')):
                    image_path = os.path.join(folder_full_path, filename)
                    images.append((filename, image_path))
            folder_images[folder_name] = images

    return folder_images


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print("START")
    screenshots_folder = 'data_screenshots'
    results = process_screenshots_folder(screenshots_folder)

    # Print extracted text from each screenshot
    with open('../results.txt', 'w', encoding='utf-8') as f:
        for folder, files in results.items():
            f.write(f'\nFolder: {folder}\n')
            for filename, text in files.items():
                f.write(f'\nText extracted from {filename}:\n')
                f.write(f'{text}\n')
