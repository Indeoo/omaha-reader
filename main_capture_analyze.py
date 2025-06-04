#!/usr/bin/env python3
"""
Script that captures windows using capture_utils and analyzes them with PlayerCardReader.
Outputs results to text files with detailed card detection information.
"""

import os
import cv2
import numpy as np
from datetime import datetime
from typing import List, Dict, Any
from PIL import Image

from src.capture.capture_utils import capture_windows
from src.cv.opencv_utils import pil_to_cv2
from src.player_card_reader import PlayerCardReader
from src.readed_card import ReadedCard


def analyze_image_with_player_reader(image: np.ndarray, image_name: str,
                                     player_card_reader: PlayerCardReader) -> Dict[str, Any]:
    """
    Analyze a single image with PlayerCardReader

    Args:
        image: OpenCV image (BGR format)
        image_name: Name/description of the image
        player_card_reader: PlayerCardReader instance

    Returns:
        Dictionary containing analysis results
    """
    result = {
        'image_name': image_name,
        'cards_found': 0,
        'cards': [],
        'error': None,
        'image_dimensions': image.shape[:2] if image is not None else None
    }

    try:
        # Read cards using PlayerCardReader
        readed_cards = player_card_reader.read(image)
        result['cards_found'] = len(readed_cards)

        # Store detailed card information
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

        print(f"    ✅ {image_name}: {len(readed_cards)} cards detected")

    except Exception as e:
        result['error'] = str(e)
        print(f"    ❌ Error analyzing {image_name}: {str(e)}")

    return result


def write_analysis_results_to_file(results: List[Dict[str, Any]], output_path: str,
                                   timestamp: str, total_images: int) -> None:
    """
    Write all analysis results to a single comprehensive text file

    Args:
        results: List of analysis result dictionaries
        output_path: Path to output file
        timestamp: Timestamp of the capture session
        total_images: Total number of images processed
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("WINDOW CAPTURE & PLAYER CARD ANALYSIS RESULTS\n")
            f.write("=" * 80 + "\n")
            f.write(f"Capture Timestamp: {timestamp}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Images Processed: {total_images}\n")
            f.write("=" * 80 + "\n\n")

            # Overall summary
            total_cards = sum(result['cards_found'] for result in results)
            successful_analyses = sum(1 for result in results if result['error'] is None)
            failed_analyses = total_images - successful_analyses

            f.write("📊 OVERALL SUMMARY\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total images captured: {total_images}\n")
            f.write(f"Successfully analyzed: {successful_analyses}\n")
            f.write(f"Failed analyses: {failed_analyses}\n")
            f.write(f"Total cards detected: {total_cards}\n")

            if successful_analyses > 0:
                avg_cards = total_cards / successful_analyses
                f.write(f"Average cards per successful image: {avg_cards:.2f}\n")

            # Card distribution across all images
            if total_cards > 0:
                all_card_counts = {}
                all_scores = []
                all_scales = []

                for result in results:
                    if result['error'] is None:
                        for card in result['cards']:
                            # Count card types
                            template_name = card['template_name']
                            all_card_counts[template_name] = all_card_counts.get(template_name, 0) + 1

                            # Collect scores and scales
                            all_scores.append(card['match_score'])
                            if card['scale']:
                                all_scales.append(card['scale'])

                f.write(f"\n🃏 CARD DISTRIBUTION (All Images)\n")
                f.write("-" * 40 + "\n")
                for card_name, count in sorted(all_card_counts.items()):
                    f.write(f"{card_name}: {count} occurrence{'s' if count > 1 else ''}\n")

                f.write(f"\n📈 DETECTION STATISTICS\n")
                f.write("-" * 40 + "\n")
                f.write(f"Average match score: {sum(all_scores) / len(all_scores):.4f}\n")
                f.write(f"Score range: {min(all_scores):.4f} - {max(all_scores):.4f}\n")

                if all_scales:
                    f.write(f"Average scale: {sum(all_scales) / len(all_scales):.2f}\n")
                    f.write(f"Scale range: {min(all_scales):.2f} - {max(all_scales):.2f}\n")

            f.write("\n")

            # Detailed results for each image
            f.write("📝 DETAILED RESULTS BY IMAGE\n")
            f.write("=" * 80 + "\n")

            for i, result in enumerate(results, 1):
                f.write(f"\n📷 IMAGE {i}: {result['image_name']}\n")
                f.write("-" * 60 + "\n")

                if result['image_dimensions']:
                    height, width = result['image_dimensions']
                    f.write(f"Dimensions: {width}x{height} pixels\n")

                if result['error']:
                    f.write(f"❌ ERROR: {result['error']}\n")
                    continue

                f.write(f"Cards detected: {result['cards_found']}\n")

                if result['cards']:
                    # Image-specific card distribution
                    image_card_counts = {}
                    for card in result['cards']:
                        template_name = card['template_name']
                        image_card_counts[template_name] = image_card_counts.get(template_name, 0) + 1

                    f.write("Card types: ")
                    f.write(", ".join([f"{name}({count})" for name, count in sorted(image_card_counts.items())]))
                    f.write("\n")

                    # Individual card details
                    f.write("\nDetailed card information:\n")
                    for card in result['cards']:
                        f.write(f"  {card['index']}. {card['template_name']}\n")
                        f.write(f"     Score: {card['match_score']:.4f}\n")
                        f.write(f"     Center: {card['center']}\n")
                        f.write(f"     Size: {card['bounding_rect'][2]}x{card['bounding_rect'][3]}\n")
                        if card['scale']:
                            f.write(f"     Scale: {card['scale']}\n")
                        f.write(f"     Area: {card['area']}\n")
                        f.write("\n")
                else:
                    f.write("No cards detected in this image.\n")

            f.write("\n" + "=" * 80 + "\n")
            f.write("End of Analysis Report\n")
            f.write("=" * 80 + "\n")

    except Exception as e:
        print(f"❌ Error writing results file: {str(e)}")
        raise


def main():
    """
    Main function that captures windows and analyzes them for player cards
    """
    print("🚀 Starting Window Capture & Player Card Analysis")
    print("=" * 60)

    # Configuration
    templates_dir = "resources/templates/player_cards/"
    output_dir = "resources/capture_analysis_results"

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Initialize PlayerCardReader
    print("🎯 Initializing PlayerCardReader...")
    try:
        player_card_reader = PlayerCardReader(templates_dir=templates_dir)

        if not player_card_reader.templates:
            print("❌ No templates loaded! Please check the templates directory.")
            print(f"Templates directory: {templates_dir}")
            return

        print(f"✅ Loaded {len(player_card_reader.templates)} templates")
        print(f"Templates: {list(player_card_reader.templates.keys())}")

    except Exception as e:
        print(f"❌ Error initializing PlayerCardReader: {str(e)}")
        return

    # Capture windows
    print("\n📸 Capturing windows...")
    try:
        captured_images, windows = capture_windows()
        print(f"✅ Captured {len(captured_images)} images")

        if not captured_images:
            print("❌ No images captured. Exiting.")
            return

    except Exception as e:
        print(f"❌ Error capturing windows: {str(e)}")
        return

    # Create timestamped output file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"capture_analysis_{timestamp}.txt"
    output_path = os.path.join(output_dir, output_filename)

    print(f"\n🔍 Analyzing {len(captured_images)} captured images...")
    print(f"📁 Results will be saved to: {output_path}")

    # Analyze each captured image
    analysis_results = []

    for i, captured_item in enumerate(captured_images, 1):
        image_name = captured_item['filename']
        pil_image = captured_item['image']

        print(f"🔍 Analyzing image {i}/{len(captured_images)}: {image_name}")

        try:
            # Convert PIL image to OpenCV format
            cv2_image = pil_to_cv2(pil_image)

            # Analyze with PlayerCardReader
            result = analyze_image_with_player_reader(cv2_image, image_name, player_card_reader)
            analysis_results.append(result)

        except Exception as e:
            print(f"    ❌ Error processing {image_name}: {str(e)}")
            # Add error result
            error_result = {
                'image_name': image_name,
                'cards_found': 0,
                'cards': [],
                'error': str(e),
                'image_dimensions': None
            }
            analysis_results.append(error_result)

    # Write results to file
    print(f"\n💾 Writing analysis results...")
    try:
        write_analysis_results_to_file(analysis_results, output_path, timestamp, len(captured_images))
        print(f"✅ Results written to: {output_path}")

    except Exception as e:
        print(f"❌ Error writing results: {str(e)}")
        return

    # Print final summary
    total_cards = sum(result['cards_found'] for result in analysis_results)
    successful_analyses = sum(1 for result in analysis_results if result['error'] is None)

    print("\n" + "=" * 60)
    print("🎉 CAPTURE & ANALYSIS COMPLETE!")
    print("=" * 60)
    print(f"Images captured: {len(captured_images)}")
    print(f"Images successfully analyzed: {successful_analyses}")
    print(f"Total cards detected: {total_cards}")

    if successful_analyses > 0:
        avg_cards = total_cards / successful_analyses
        print(f"Average cards per image: {avg_cards:.2f}")

    print(f"📄 Detailed results saved to: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()