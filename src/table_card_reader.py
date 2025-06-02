
import cv2
import numpy as np
from typing import List, Tuple, Dict

from src.card_reader import CardReader
from src.readed_card import ReadedCard
from src.utils.image_preprocessor import ImagePreprocessor
from src.utils.save_utils import save_detected_cards
from src.utils.template_loader import load_templates
from src.utils.template_validator import extract_card, match_card_to_templates


class TableCardReader(CardReader):
    def __init__(self,
                 table_card_area_range: Tuple[int, int] = (1000, 25000),
                 aspect_ratio_range: Tuple[float, float] = (0.5, 0.85),
                 template_dir="resources/templates/table_cards/", ):
        self.table_card_area_range = table_card_area_range
        self.aspect_ratio_range = aspect_ratio_range
        self.image_preprocessor = ImagePreprocessor()
        self.templates = load_templates(template_dir)

    def read(self, image: np.ndarray) -> List[ReadedCard]:
        """
        Detect table cards and return as ReadedCard objects

        Returns:
            List of ReadedCard objects
        """
        # Detect cards
        detected_cards = self.detect(image)

        # Print results
        print(f"Detected {len(detected_cards)} table cards")
        for i, card in enumerate(detected_cards):
            print(f"Table card {i + 1}: area={card['area']:.0f}, center={card['center']}")

        # Convert to ReadedCard objects with validation
        readed_cards = []
        #extracted_cards = []

        for i, card in enumerate(detected_cards):
            # Extract card region
            card_region = extract_card(image, card)
            #extracted_cards.append(card_region)

            # Validate against templates
            match_name, score, is_valid = match_card_to_templates(card_region, self.templates, threshold=0.6)

            # Create ReadedCard object
            x, y, w, h = card['bounding_rect']
            readed_card = ReadedCard(
                card_index=i,
                card_region=card_region,
                bounding_rect=card['bounding_rect'],
                center=card['center'],
                area=card['area'],
                template_name=match_name,
                match_score=score,
                is_valid=is_valid,
                contour=card['contour'],
                rotated_rect=card['rotated_rect'],
                box_points=card['box_points']
            )
            readed_cards.append(readed_card)

        # Save detected cards
        save_detected_cards(readed_cards)

        # Print validation results
        self._print_validation_results(readed_cards)

        return readed_cards

    def detect(self, image: np.ndarray) -> List[Dict]:
        """
        Detect all cards in the image and classify them
        Updated for rounded rectangle card detection

        Returns:
            List of dictionaries containing card info
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

    def draw_detected_cards(self, image: np.ndarray, readed_cards: List[ReadedCard]) -> np.ndarray:
        """
        Draw detected cards on the image for visualization
        """
        result_image = image.copy()

        # Draw table cards in red
        for card in readed_cards:
            cv2.drawContours(result_image, [card.box_points], -1, (0, 0, 255), 2)
            cv2.putText(result_image, 'Table', card.center,
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        return result_image

    def _print_validation_results(self, readed_cards: List[ReadedCard], threshold=0.6):
        """Print validation results in the same format as before"""
        print(f"🔍 Starting validation with threshold: {threshold}")
        print(f"🎯 Validating {len(readed_cards)} detected cards...")

        valid_matches = []
        invalid_matches = []

        for i, card in enumerate(readed_cards):
            status = "✓ VALID" if card.is_valid else "✗ INVALID"
            match_name = card.template_name or 'NO_MATCH'
            print(f"Card {i + 1:2d}: {match_name:>8s} | Score: {card.match_score:.3f} | {status}")

            if card.is_valid:
                valid_matches.append(f"{match_name} ({card.match_score:.3f})")
            else:
                invalid_matches.append(f"{match_name} ({card.match_score:.3f})")

        # Calculate summary
        total_cards = len(readed_cards)
        valid_cards = sum(1 for card in readed_cards if card.is_valid)
        validation_rate = (valid_cards / total_cards * 100) if total_cards > 0 else 0

        # Enhanced summary logging
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Total cards detected: {total_cards}")
        print(f"Valid cards: {valid_cards}")
        print(f"Invalid cards: {total_cards - valid_cards}")
        print(f"Validation rate: {validation_rate:.1f}%")

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