#!/usr/bin/env python3
"""
Script to analyze player cards from screenshot folders using PlayerCardReader.
Iterates over all timestamp folders in resources/data_screenshots and processes
all images, writing results to resources/player_results/{timestamp}/{image_name}.txt
"""

import os
from typing import Dict, Any
from datetime import datetime

from src.core.reader.omaha_card_reader import PlayerCardReader
from src.core.utils.opencv_utils import load_templates, read_cv2_image


def process_single_image(image_path: str, image_name: str, player_card_reader: PlayerCardReader) -> Dict[str, Any]:
    """
    Process a single image and return results

    Args:
        image_path: Full path to the image
        image_name: Name of the image file
        player_card_reader: PlayerCardReader instance

    Returns:
        Dictionary containing processing results for this image
    """
    result = {
        'filename': image_name,
        'cards_found': 0,
        'cards': [],
        'error': None
    }

    try:
        # Load image
        image = read_cv2_image(image_path)
        if image is None:
            result['error'] = f"Could not load image: {image_name}"
            return result

        # Read cards
        readed_cards = player_card_reader.read(image)
        result['cards_found'] = len(readed_cards)

        # Store card details
        for i, card in enumerate(readed_cards):
            card_info = {
                'index': i + 1,
                'template_name': card.template_name,
                'match_score': round(card.match_score, 4),
                'center': card.center,
                'bounding_rect': card.bounding_rect,
                'scale': round(card.scale, 2) if card.scale else None,
                'area': round(card.area, 2)
            }
            result['cards'].append(card_info)

        print(f"    ✅ {image_name}: {len(readed_cards)} cards found")

    except Exception as e:
        result['error'] = str(e)
        print(f"    ❌ Error processing {image_name}: {str(e)}")

    return result


def write_image_results_to_file(image_result: Dict[str, Any], output_path: str, timestamp: str) -> None:
    """
    Write processing results for a single image to a text file

    Args:
        image_result: Results dictionary for single image
        output_path: Path to output file
        timestamp: Source folder timestamp
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write(f"PLAYER CARD ANALYSIS RESULTS\n")
            f.write(f"Source Folder Timestamp: {timestamp}\n")
            f.write(f"Source File: {image_result['filename']}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")

            # Summary for this image
            f.write("📊 SUMMARY\n")
            f.write("-" * 40 + "\n")
            f.write(f"Source file: {image_result['filename']}\n")
            f.write(f"Cards found: {image_result['cards_found']}\n")

            if image_result['error']:
                f.write(f"Error: {image_result['error']}\n")
                return

            if image_result['cards']:
                # Card statistics
                all_scores = [card['match_score'] for card in image_result['cards']]
                all_scales = [card['scale'] for card in image_result['cards'] if card['scale']]

                f.write(f"Average match score: {sum(all_scores) / len(all_scores):.4f}\n")
                f.write(f"Score range: {min(all_scores):.4f} - {max(all_scores):.4f}\n")

                if all_scales:
                    f.write(f"Average scale: {sum(all_scales) / len(all_scales):.2f}\n")
                    f.write(f"Scale range: {min(all_scales):.2f} - {max(all_scales):.2f}\n")

                # Card distribution
                card_counts = {}
                for card in image_result['cards']:
                    template_name = card['template_name']
                    card_counts[template_name] = card_counts.get(template_name, 0) + 1

                f.write("\n🃏 DETECTED CARDS\n")
                f.write("-" * 40 + "\n")
                for card_name, count in sorted(card_counts.items()):
                    f.write(f"{card_name}: {count} occurrence{'s' if count > 1 else ''}\n")

                f.write("\n")

            # Detailed results
            f.write("📝 DETAILED RESULTS\n")
            f.write("=" * 80 + "\n")
            f.write(f"\n📷 SOURCE: {image_result['filename']}\n")
            f.write("-" * 60 + "\n")

            if image_result['error']:
                f.write(f"❌ ERROR: {image_result['error']}\n")
                return

            if image_result['cards']:
                f.write("\nDetected cards:\n")
                for card in image_result['cards']:
                    f.write(f"  {card['index']}. {card['template_name']} (SOURCE: {image_result['filename']})\n")
                    f.write(f"     Score: {card['match_score']:.4f}\n")
                    f.write(f"     Center: {card['center']}\n")
                    f.write(f"     Size: {card['bounding_rect'][2]}x{card['bounding_rect'][3]}\n")
                    if card['scale']:
                        f.write(f"     Scale: {card['scale']}\n")
                    f.write(f"     Area: {card['area']}\n")
                    f.write("\n")
            else:
                f.write("No cards detected.\n")

    except Exception as e:
        print(f"  ❌ Error writing file {output_path}: {str(e)}")
        raise


def process_timestamp_folder(folder_path: str, timestamp: str, player_card_reader: PlayerCardReader,
                             output_base_dir: str) -> Dict[str, Any]:
    """
    Process all images in a timestamp folder and create individual result files

    Args:
        folder_path: Path to the timestamp folder
        timestamp: Timestamp string (folder name)
        player_card_reader: PlayerCardReader instance
        output_base_dir: Base output directory

    Returns:
        Dictionary containing processing summary
    """
    # Create output directory for this timestamp
    timestamp_output_dir = os.path.join(output_base_dir, timestamp)
    os.makedirs(timestamp_output_dir, exist_ok=True)

    # Get all image files in the folder
    image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')
    image_files = [f for f in os.listdir(folder_path)
                   if f.lower().endswith(image_extensions)]

    summary = {
        'timestamp': timestamp,
        'total_images': len(image_files),
        'processed_images': 0,
        'total_cards_found': 0,
        'files_created': []
    }

    print(f"  📁 Processing {len(image_files)} images in folder: {timestamp}")
    print(f"  📂 Output directory: {timestamp_output_dir}")

    for image_file in sorted(image_files):
        image_path = os.path.join(folder_path, image_file)

        # Process the image
        image_result = process_single_image(image_path, image_file, player_card_reader)

        # Create output filename (remove extension and add .txt)
        base_name = os.path.splitext(image_file)[0]
        output_filename = f"{base_name}.txt"
        output_path = os.path.join(timestamp_output_dir, output_filename)

        # Write results to individual file
        try:
            write_image_results_to_file(image_result, output_path, timestamp)
            summary['files_created'].append(output_filename)
            print(f"    📄 Created: {output_filename}")
        except Exception as e:
            print(f"    ❌ Failed to create file for {image_file}: {str(e)}")
            continue

        # Update summary
        summary['processed_images'] += 1
        summary['total_cards_found'] += image_result['cards_found']

    return summary


def main():
    """
    Main function to process all timestamp folders
    """
    # Configuration
    screenshots_dir = "../../../resources/data_screenshots"
    output_dir = "resources/player_results"
    templates_dir = "../../../resources/templates/player_cards/"
    templates = load_templates(templates_dir)

    # Create base output directory
    os.makedirs(output_dir, exist_ok=True)

    # Initialize player card reader
    print("🚀 Initializing PlayerCardReader...")
    player_card_reader = PlayerCardReader(templates)

    if not player_card_reader.templates:
        print("❌ No templates loaded! Please check the templates directory.")
        return

    print(f"✅ Loaded {len(player_card_reader.templates)} templates")

    # Check if screenshots directory exists
    if not os.path.exists(screenshots_dir):
        print(f"❌ Screenshots directory not found: {screenshots_dir}")
        return

    # Get all timestamp folders
    timestamp_folders = [f for f in os.listdir(screenshots_dir)
                         if os.path.isdir(os.path.join(screenshots_dir, f))]

    if not timestamp_folders:
        print(f"❌ No timestamp folders found in {screenshots_dir}")
        return

    timestamp_folders.sort()
    print(f"📁 Found {len(timestamp_folders)} timestamp folders")

    # Process each timestamp folder
    overall_stats = {
        'total_folders': len(timestamp_folders),
        'processed_folders': 0,
        'total_images': 0,
        'total_cards': 0,
        'total_files_created': 0
    }

    for timestamp in timestamp_folders:
        folder_path = os.path.join(screenshots_dir, timestamp)

        print(f"\n🔄 Processing folder: {timestamp}")

        try:
            # Process the folder
            summary = process_timestamp_folder(folder_path, timestamp, player_card_reader, output_dir)

            # Update overall stats
            overall_stats['processed_folders'] += 1
            overall_stats['total_images'] += summary['processed_images']
            overall_stats['total_cards'] += summary['total_cards_found']
            overall_stats['total_files_created'] += len(summary['files_created'])

            print(f"✅ Folder completed: {timestamp}")
            print(
                f"   📊 Summary: {summary['processed_images']} images, {summary['total_cards_found']} cards, {len(summary['files_created'])} files created")

        except Exception as e:
            print(f"❌ Error processing folder {timestamp}: {str(e)}")

    # Print final summary
    print("\n" + "=" * 80)
    print("🎉 PROCESSING COMPLETE!")
    print("=" * 80)
    print(f"Folders processed: {overall_stats['processed_folders']}/{overall_stats['total_folders']}")
    print(f"Total images processed: {overall_stats['total_images']}")
    print(f"Total cards detected: {overall_stats['total_cards']}")
    print(f"Total result files created: {overall_stats['total_files_created']}")

    if overall_stats['total_images'] > 0:
        avg_cards = overall_stats['total_cards'] / overall_stats['total_images']
        print(f"Average cards per image: {avg_cards:.2f}")

    print(f"📁 Results saved in: {output_dir}")
    print(f"📂 Each timestamp has its own subfolder with individual .txt files per image")


if __name__ == "__main__":
    main()