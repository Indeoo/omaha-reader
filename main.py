# This is a sample Python script.

import pytesseract
from PIL import Image
import os


def extract_text_from_screenshot(image_path):
    # Open image with PIL
    img = Image.open(image_path)

    # Extract text from image using pytesseract
    text = pytesseract.image_to_string(img)
    return text


def process_screenshots_folder(folder_path):
    results = {}

    # Loop through all folders in the main folder
    for folder_name in os.listdir(folder_path):
        print(folder_name)
        folder_full_path = os.path.join(folder_path, folder_name)

        if os.path.isdir(folder_full_path):
            results[folder_name] = {}

            # Loop through all files in each folder
            for filename in os.listdir(folder_full_path):
                if filename.endswith(('.png', '.jpg', '.jpeg')):
                    image_path = os.path.join(folder_full_path, filename)
                    text = extract_text_from_screenshot(image_path)
                    results[folder_name][filename] = text

    return results

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    screenshots_folder = 'data_screenshots'
    results = process_screenshots_folder(screenshots_folder)

    # Print extracted text from each screenshot
    with open('results.txt', 'w', encoding='utf-8') as f:
        for folder, files in results.items():
            f.write(f'\nFolder: {folder}\n')
            for filename, text in files.items():
                f.write(f'\nText extracted from {filename}:\n')
                f.write(f'{text}\n')
