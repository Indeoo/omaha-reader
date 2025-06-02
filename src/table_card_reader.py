import cv2
import numpy as np
from typing import List, Tuple, Dict
import matplotlib.pyplot as plt

from src.utils.image_preprocessor import ImagePreprocessor
from src.utils.save_utils import save_detected_cards
from src.utils.template_loader import load_templates
from src.utils.template_validator import extract_card, match_card_to_templates


class TableCardReader:
    def __init__(self,
                 table_card_area_range: Tuple[int, int] = (15000, 50000),
                 aspect_ratio_range: Tuple[float, float] = (0.6, 0.8)):
        """
        Initialize the poker card detector

        Args:
            table_card_area_range: Min and max area for table cards
            aspect_ratio_range: Expected aspect ratio range for cards (width/height)
        """
        self.table_card_area_range = table_card_area_range
        self.aspect_ratio_range = aspect_ratio_range
        self.image_preprocessor = ImagePreprocessor()

    def is_card_like_contour(self, contour: np.ndarray, image_shape: Tuple[int, int]) -> bool:
        """
        Check if a contour looks like a card based on shape properties
        Updated for rounded rectangle card borders
        """
        # Calculate area
        area = cv2.contourArea(contour)

        # Check if area is in expected range for any card type
        min_area = min(self.table_card_area_range[0], self.table_card_area_range[0])
        max_area = max(self.table_card_area_range[1], self.table_card_area_range[1])

        if not (min_area <= area <= max_area):
            return False

        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(contour)

        # Filter out very small or very large contours relative to image size
        image_area = image_shape[0] * image_shape[1]
        if area < image_area * 0.001 or area > image_area * 0.3:
            return False

        # Check aspect ratio (cards are typically rectangular)
        aspect_ratio = w / h if h > 0 else 0

        # Allow for both orientations and be more flexible with rounded corners
        valid_aspect = (0.5 <= aspect_ratio <= 0.9) or (1.1 <= aspect_ratio <= 2.0)
        if not valid_aspect:
            return False

        # Check if contour is reasonably filled (not just an outline)
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        if hull_area > 0:
            solidity = area / hull_area
            if solidity < 0.7:  # Allow for rounded corners
                return False

        # Check if the contour has reasonable dimensions
        if w < 20 or h < 30:  # Too small to be a card
            return False

        return True

    def detect_cards(self, image: np.ndarray) -> Dict[str, List[Dict]]:
        """
        Detect all cards in the image and classify them
        Updated for rounded rectangle card detection

        Returns:
            Dictionary with 'table_cards' lists containing card info
        """
        # Preprocess image
        processed = self.image_preprocessor.preprocess_image(image)

        # Find contours
        contours, _ = cv2.findContours(processed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        table_cards = []

        for contour in contours:
            if self.is_card_like_contour(contour, image.shape[:2]):
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)

                # Get rotated rectangle for better representation
                rect = cv2.minAreaRect(contour)
                box = cv2.boxPoints(rect)
                box = np.array(box, dtype=np.int32)

                card_info = {
                    'contour': contour,
                    'bounding_rect': (x, y, w, h),
                    'rotated_rect': rect,
                    'box_points': box,
                    'area': cv2.contourArea(contour),
                    'center': (int(rect[0][0]), int(rect[0][1]))
                }

                table_cards.append(card_info)

        return table_cards

    def draw_detected_cards(self, image: np.ndarray, detected_cards: Dict) -> np.ndarray:
        """
        Draw detected cards on the image for visualization
        """
        result_image = image.copy()

        # Draw table cards in red
        for card in detected_cards:
            cv2.drawContours(result_image, [card['box_points']], -1, (0, 0, 255), 2)
            cv2.putText(result_image, 'Table', card['center'],
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        return result_image

    def extract_card_region(self, image: np.ndarray, card_info: Dict) -> np.ndarray:
        extract_card(image, card_info)

    def validate_detected_cards(self, image, detected_cards, template_dir, threshold=0.6):
        """
        Validate detected cards against templates

        Args:
            image: Original image (numpy array)
            detected_cards: Output from your detect_cards() function
            template_dir: Directory containing template images
            threshold: Minimum match score (0.0-1.0)

        Returns:
            Dictionary with validation results
        """
        print(f"🔍 Starting validation with threshold: {threshold}")
        print(f"📁 Loading templates from: {template_dir}")

        # Load templates
        templates = load_templates(template_dir)

        if not templates:
            print(f"❌ No templates loaded from {template_dir}")
            return {"error": "No templates loaded"}

        print(f"✅ Loaded {len(templates)} templates: {list(templates.keys())}")

        results = {
            "table_cards": [],
            "summary": {"total": 0, "valid": 0, "invalid": 0}
        }

        valid_matches = []
        invalid_matches = []

        # Validate table cards
        print(f"🎯 Validating {len(detected_cards)} detected cards...")

        for i, card in enumerate(detected_cards):
            card_region = extract_card(image, card)
            match_name, score, is_valid = match_card_to_templates(card_region, templates, threshold)

            result = {
                "card_index": i,
                "match": match_name,
                "score": score,
                "is_valid": is_valid,
                "card_region": card_region
            }
            results["table_cards"].append(result)

            # Detailed logging for each card
            status = "✓ VALID" if is_valid else "✗ INVALID"
            print(f"Card {i + 1:2d}: {match_name or 'NO_MATCH':>8s} | Score: {score:.3f} | {status}")

            # Collect results for summary
            if is_valid:
                valid_matches.append(f"{match_name} ({score:.3f})")
            else:
                invalid_matches.append(f"{match_name or 'NO_MATCH'} ({score:.3f})")

        # Calculate summary
        total_cards = len(results["table_cards"])
        valid_cards = sum(1 for card in results["table_cards"] if card["is_valid"])

        results["summary"] = {
            "total": total_cards,
            "valid": valid_cards,
            "invalid": total_cards - valid_cards,
            "validation_rate": (valid_cards / total_cards * 100) if total_cards > 0 else 0
        }

        # Enhanced summary logging
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Total cards detected: {total_cards}")
        print(f"Valid cards: {valid_cards}")
        print(f"Invalid cards: {total_cards - valid_cards}")
        print(f"Validation rate: {results['summary']['validation_rate']:.1f}%")

        if valid_matches:
            print(f"\n✅ VALID CARDS ({len(valid_matches)}):")
            for i, match in enumerate(valid_matches, 1):
                print(f"  {i:2d}. {match}")

        if invalid_matches:
            print(f"\n❌ INVALID CARDS ({len(invalid_matches)}):")
            for i, match in enumerate(invalid_matches, 1):
                print(f"  {i:2d}. {match}")

        if not valid_matches and not invalid_matches:
            print("⚠️  No cards were processed!")

        print("=" * 60)

        return results


def read_table_card(image, template_dir):
    table_card_reader = TableCardReader(
        table_card_area_range=(1000, 25000),  # Larger cards
        aspect_ratio_range=(0.5, 0.85)  # Typical card proportions
    )

    # Detect cards
    detected_cards = table_card_reader.detect_cards(image)

    # Print results
    print(f"Detected {len(detected_cards)} table cards")

    for i, card in enumerate(detected_cards):
        print(f"Table card {i + 1}: area={card['area']:.0f}, center={card['center']}")

    # Draw results
    result_image = table_card_reader.draw_detected_cards(image, detected_cards)

    extracted_cards = []

    for card in detected_cards:
        card_region = extract_card(image, card)
        extracted_cards.append(card_region)

    save_detected_cards(extracted_cards)
    table_card_reader.validate_detected_cards(result_image, detected_cards, template_dir)

    process_results(detected_cards, table_card_reader, image, result_image)


def process_results(detected_cards, detector, image, result_image):
    # Display results (if running in an environment with display)
    try:
        plt.figure(figsize=(15, 10))

        # Show original image
        plt.subplot(2, 2, 1)
        plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        plt.title('Original Image')
        plt.axis('off')

        # Show preprocessed image
        plt.subplot(2, 2, 2)
        processed = detector.image_preprocessor.preprocess_image(image)
        plt.imshow(processed, cmap='gray')
        plt.title('Preprocessed (Edge Detection)')
        plt.axis('off')

        # Show detected cards
        plt.subplot(2, 2, 3)
        plt.imshow(cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB))
        plt.title('Detected Cards')
        plt.axis('off')

        # Show individual card regions
        plt.subplot(2, 2, 4)
        if detected_cards['table_cards']:
            # Extract first detected card as example
            all_cards = detected_cards['table_cards']
            if all_cards:
                sample_card = detector.extract_card_region(image, all_cards[0])
                plt.imshow(cv2.cvtColor(sample_card, cv2.COLOR_BGR2RGB))
                plt.title('Sample Extracted Card')
        plt.axis('off')

        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"Display not available: {e}")
        print("But detection completed successfully")
