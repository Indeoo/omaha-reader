import os
import cv2
from pathlib import Path
from datetime import datetime
from src.table_card_reader import TableCardReader
from src.utils.template_validator import extract_card


def process_all_screenshots(
        screenshots_dir: str = "resources/data_screenshots",
        output_dir: str = "resources/card_result",
        templates_dir: str = "resources/templates/full_cards"
):
    """
    Process all screenshot folders and detect cards in each image

    Args:
        screenshots_dir: Directory containing timestamped folders with screenshots
        output_dir: Base directory for saving detected cards
        templates_dir: Directory containing card templates
    """

    # Initialize the card reader
    print(f"🎯 Initializing TableCardReader with templates from: {templates_dir}")
    table_card_reader = TableCardReader(template_dir=templates_dir)

    # Create output directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamped_output_dir = Path(output_dir) / f"detection_{timestamp}"
    os.makedirs(timestamped_output_dir, exist_ok=True)

    print(f"💾 Results will be saved to: {timestamped_output_dir}")

    # Get all timestamp folders
    screenshots_path = Path(screenshots_dir)
    if not screenshots_path.exists():
        print(f"❌ Screenshots directory not found: {screenshots_dir}")
        return

    timestamp_folders = [f for f in screenshots_path.iterdir() if f.is_dir()]
    timestamp_folders.sort()  # Sort for consistent processing order

    print(f"📁 Found {len(timestamp_folders)} timestamp folders to process")

    total_images_processed = 0
    total_cards_detected = 0

    for folder in timestamp_folders:
        folder_name = folder.name
        print(f"\n📂 Processing folder: {folder_name}")

        # Get all PNG images in the folder
        image_files = list(folder.glob("*.png"))
        if not image_files:
            print(f"   ⚠️  No PNG images found in {folder_name}")
            continue

        print(f"   🖼️  Found {len(image_files)} images")

        # Create output folder for this timestamp
        folder_output_dir = timestamped_output_dir / folder_name
        os.makedirs(folder_output_dir, exist_ok=True)

        folder_cards_count = 0

        # Process each image in the folder
        for image_file in image_files:
            try:
                # Load image
                image = cv2.imread(str(image_file))
                if image is None:
                    print(f"   ❌ Could not load image: {image_file.name}")
                    continue

                print(f"   🔍 Processing: {image_file.name}")

                # Detect cards using TableCardReader
                detected_cards = table_card_reader.detect(image)

                if not detected_cards:
                    print(f"      No cards detected in {image_file.name}")
                    continue

                print(f"      ✅ Detected {len(detected_cards)} cards")

                # Extract and save each detected card
                for i, card_info in enumerate(detected_cards):
                    try:
                        # Extract card region
                        card_region = extract_card(image, card_info)

                        # Create filename: card_{i}.png
                        card_filename = f"card_{i + 1}.png"
                        card_output_path = folder_output_dir / f"{image_file.stem}_{card_filename}"

                        # Save the card
                        cv2.imwrite(str(card_output_path), card_region)
                        print(f"         💾 Saved: {card_output_path.name}")

                        folder_cards_count += 1
                        total_cards_detected += 1

                    except Exception as e:
                        print(f"         ❌ Error extracting card {i + 1}: {e}")

                total_images_processed += 1

            except Exception as e:
                print(f"   ❌ Error processing {image_file.name}: {e}")

        print(f"   📊 Folder summary: {folder_cards_count} cards extracted from {len(image_files)} images")

    # Print overall summary
    print(f"\n" + "=" * 60)
    print(f"🎉 BATCH PROCESSING COMPLETE")
    print(f"=" * 60)
    print(f"📁 Folders processed: {len(timestamp_folders)}")
    print(f"🖼️  Images processed: {total_images_processed}")
    print(f"🃏 Total cards detected: {total_cards_detected}")
    print(f"💾 Results saved to: {timestamped_output_dir}")
    print(f"=" * 60)


def process_single_folder(
        folder_path: str,
        output_dir: str = "resources/card_result",
        templates_dir: str = "resources/templates/full_cards"
):
    """
    Process a single timestamp folder for testing

    Args:
        folder_path: Path to the specific timestamp folder
        output_dir: Base directory for saving detected cards
        templates_dir: Directory containing card templates
    """

    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        print(f"❌ Folder not found: {folder_path}")
        return

    print(f"🎯 Processing single folder: {folder.name}")

    # Initialize the card reader
    table_card_reader = TableCardReader(template_dir=templates_dir)

    # Create output directory
    folder_output_dir = Path(output_dir) / folder.name
    os.makedirs(folder_output_dir, exist_ok=True)

    # Get all PNG images
    image_files = list(folder.glob("*.png"))
    print(f"🖼️  Found {len(image_files)} images to process")

    total_cards = 0

    for image_file in image_files:
        try:
            # Load and process image
            image = cv2.imread(str(image_file))
            if image is None:
                continue

            print(f"🔍 Processing: {image_file.name}")
            detected_cards = table_card_reader.detect(image)

            if detected_cards:
                print(f"   ✅ Found {len(detected_cards)} cards")

                # Save each card
                for i, card_info in enumerate(detected_cards):
                    card_region = extract_card(image, card_info)
                    card_path = folder_output_dir / f"{image_file.stem}_card_{i + 1}.png"
                    cv2.imwrite(str(card_path), card_region)
                    total_cards += 1
            else:
                print(f"   No cards detected")

        except Exception as e:
            print(f"❌ Error processing {image_file.name}: {e}")

    print(f"✅ Complete! Extracted {total_cards} cards to {folder_output_dir}")


if __name__ == "__main__":
    # Process all screenshot folders
    process_all_screenshots()

    # Example of processing a single folder (uncomment to use):
    # process_single_folder("resources/data_screenshots/2024_12_15_14_30_25")