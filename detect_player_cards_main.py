#!/usr/bin/env python3
"""
Script to analyze player cards from screenshot folders using PlayerCardReader.
Iterates over all timestamp folders in resources/data_screenshots and processes
all images, writing results to resources/player_results/{timestamp}.txt
"""

import os
import cv2
from typing import List, Dict, Any
from datetime import datetime

from src.player_card_reader import PlayerCardReader
from src.readed_card import ReadedCard


def process_timestamp_folder(folder_path: str, timestamp: str, player_card_reader: PlayerCardReader) -> Dict[str, Any]:
    """
    Process all images in a timestamp folder

    Args:
        folder_path: Path to the timestamp folder
        timestamp: Timestamp string (folder name)
        player_card_reader: PlayerCardReader instance

    Returns:
        Dictionary containing processing results
    """
    results = {
        'timestamp': timestamp,
        'total_images': 0,
        'processed_images': 0,
        'total_cards_found': 0,
        'images': {}
    }

    # Get all image files in the folder
    image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')
    image_files = [f for f in os.listdir(folder_path)
                   if f.lower().endswith(image_extensions)]

    results['total_images'] = len(image_files)

    print(f"  📁 Processing {len(image_files)} images in folder: {timestamp}")

    for image_file in sorted(image_files):
        image_path = os.path.join(folder_path, image_file)

        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                print(f"    ⚠️  Could not load image: {image_file}")
                continue

            # Read cards
            readed_cards = player_card_reader.read(image)

            # Store results
            image_results = {
                'filename': image_file,
                'cards_found': len(readed_cards),
                'cards': []
            }

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
                image_results['cards'].append(card_info)

            results['images'][image_file] = image_results
            results['processed_images'] += 1
            results['total_cards_found'] += len(readed_cards)

            print(f"    ✅ {image_file}: {len(readed_cards)} cards found")

        except Exception as e:
            print(f"    ❌ Error processing {image_file}: {str(e)}")
            results['images'][image_file] = {
                'filename': image_file,
                'error': str(e),
                'cards_found': 0,
                'cards': []
            }

    return results


def write_results_to_file(results: Dict[str, Any], output_path: str) -> None:
    """
    Write processing results to a text file

    Args:
        results: Results dictionary
        output_path: Path to output file
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        # Header
        f.write("=" * 80 + "\n")
        f.write(f"PLAYER CARD ANALYSIS RESULTS\n")
        f.write(f"Timestamp: {results['timestamp']}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")

        # Summary
        f.write("📊 SUMMARY\n")
        f.write("-" * 40 + "\n")
        f.write(f"Total images: {results['total_images']}\n")
        f.write(f"Processed images: {results['processed_images']}\n")
        f.write(f"Failed images: {results['total_images'] - results['processed_images']}\n")
        f.write(f"Total cards found: {results['total_cards_found']}\n")

        if results['processed_images'] > 0:
            avg_cards = results['total_cards_found'] / results['processed_images']
            f.write(f"Average cards per image: {avg_cards:.2f}\n")

        f.write("\n")

        # Card distribution summary
        card_counts = {}
        all_scores = []
        all_scales = []

        for image_name, image_data in results['images'].items():
            if 'error' not in image_data:
                for card in image_data['cards']:
                    template_name = card['template_name']
                    card_counts[template_name] = card_counts.get(template_name, 0) + 1
                    all_scores.append(card['match_score'])
                    if card['scale']:
                        all_scales.append(card['scale'])

        if card_counts:
            f.write("🃏 CARD DISTRIBUTION\n")
            f.write("-" * 40 + "\n")
            for card_name, count in sorted(card_counts.items()):
                f.write(f"{card_name}: {count} occurrences\n")
            f.write("\n")

        # Statistics
        if all_scores:
            f.write("📈 STATISTICS\n")
            f.write("-" * 40 + "\n")
            f.write(f"Average match score: {sum(all_scores) / len(all_scores):.4f}\n")
            f.write(f"Min match score: {min(all_scores):.4f}\n")
            f.write(f"Max match score: {max(all_scores):.4f}\n")

            if all_scales:
                f.write(f"Average scale: {sum(all_scales) / len(all_scales):.2f}\n")
                f.write(f"Scale range: {min(all_scales):.2f} - {max(all_scales):.2f}\n")
            f.write("\n")

        # Detailed results
        f.write("📝 DETAILED RESULTS\n")
        f.write("=" * 80 + "\n")

        for image_name in sorted(results['images'].keys()):
            image_data = results['images'][image_name]
            f.write(f"\n📷 IMAGE: {image_name}\n")
            f.write("-" * 60 + "\n")

            if 'error' in image_data:
                f.write(f"❌ ERROR: {image_data['error']}\n")
                continue

            f.write(f"Cards found: {image_data['cards_found']}\n")

            if image_data['cards']:
                f.write("\nDetected cards:\n")
                for card in image_data['cards']:
                    f.write(f"  {card['index']}. {card['template_name']}\n")
                    f.write(f"     Score: {card['match_score']:.4f}\n")
                    f.write(f"     Center: {card['center']}\n")
                    f.write(f"     Size: {card['bounding_rect'][2]}x{card['bounding_rect'][3]}\n")
                    if card['scale']:
                        f.write(f"     Scale: {card['scale']}\n")
                    f.write(f"     Area: {card['area']}\n")
                    f.write("\n")
            else:
                f.write("No cards detected.\n")


def main():
    """
    Main function to process all timestamp folders
    """
    # Configuration
    screenshots_dir = "resources/data_screenshots"
    output_dir = "resources/player_results"
    templates_dir = "resources/templates/player_cards/"

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Initialize player card reader
    print("🚀 Initializing PlayerCardReader...")
    player_card_reader = PlayerCardReader(templates_dir=templates_dir)

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
        'total_cards': 0
    }

    for timestamp in timestamp_folders:
        folder_path = os.path.join(screenshots_dir, timestamp)
        output_file = os.path.join(output_dir, f"{timestamp}.txt")

        print(f"\n🔄 Processing folder: {timestamp}")

        try:
            # Process the folder
            results = process_timestamp_folder(folder_path, timestamp, player_card_reader)

            # Write results
            write_results_to_file(results, output_file)

            # Update overall stats
            overall_stats['processed_folders'] += 1
            overall_stats['total_images'] += results['processed_images']
            overall_stats['total_cards'] += results['total_cards_found']

            print(f"✅ Results written to: {output_file}")
            print(f"   📊 Summary: {results['processed_images']} images, {results['total_cards_found']} cards")

        except Exception as e:
            print(f"❌ Error processing folder {timestamp}: {str(e)}")

    # Print final summary
    print("\n" + "=" * 80)
    print("🎉 PROCESSING COMPLETE!")
    print("=" * 80)
    print(f"Folders processed: {overall_stats['processed_folders']}/{overall_stats['total_folders']}")
    print(f"Total images processed: {overall_stats['total_images']}")
    print(f"Total cards detected: {overall_stats['total_cards']}")


if __name__ == "__main__":
    main()