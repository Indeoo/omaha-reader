# 1. Create new ReadedCard class - src/readed_card.py

from typing import Tuple, Optional
import numpy as np


class ReadedCard:
    def __init__(self,
                 card_index: int,
                 card_region: np.ndarray,
                 bounding_rect: Tuple[int, int, int, int],
                 center: Tuple[int, int],
                 area: float,
                 template_name: Optional[str] = None,
                 match_score: Optional[float] = None,
                 is_valid: bool = False,
                 scale: Optional[float] = None,
                 contour: Optional[np.ndarray] = None,
                 rotated_rect: Optional[Tuple] = None,
                 box_points: Optional[np.ndarray] = None):
        """
        Unified card representation for both table and player cards

        Args:
            card_index: Index of the card in detection order
            card_region: Extracted card image region
            bounding_rect: (x, y, width, height) bounding rectangle
            center: (x, y) center coordinates
            area: Area of the card
            template_name: Name of matched template (if any)
            match_score: Template matching confidence score
            is_valid: Whether the card passed validation
            scale: Scale factor used for detection (player cards)
            contour: Card contour (table cards)
            rotated_rect: Rotated rectangle info (table cards)
            box_points: Box points for rotated rectangle (table cards)
        """
        self.card_index = card_index
        self.card_region = card_region
        self.bounding_rect = bounding_rect
        self.center = center
        self.area = area
        self.template_name = template_name
        self.match_score = match_score
        self.is_valid = is_valid
        self.scale = scale
        self.contour = contour
        self.rotated_rect = rotated_rect
        self.box_points = box_points


# 2. Modified PlayerCardReader - src/player_card_reader.py

import cv2
import numpy as np
from typing import List, Tuple, Dict

from src.card_reader import CardReader
from src.readed_card import ReadedCard
from src.utils.benchmark_utils import benchmark
from src.utils.result_processor import process_results
from src.utils.template_loader import load_templates


class PlayerCardReader(CardReader):
    DEFAULT_SEARCH_REGION = (0.0, 0.5, 1.0, 1.0)
    DEFAULT_MIN_CARD_SIZE = 20
    DEFAULT_OVERLAP_THRESHOLD = 0.3
    DEFAULT_MATCH_THRESHOLD = 0.6
    DEFAULT_SCALE_FACTORS = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5]

    def __init__(self, templates_dir: str = "resources/templates/hand_cards/"):
        """
        Template-first detector that scans the entire image directly with templates
        No preprocessing, no assumptions about colors or regions

        Args:
            templates_dir: Directory containing hand card templates
        """
        self.search_region = self.DEFAULT_SEARCH_REGION
        self.min_card_size = self.DEFAULT_MIN_CARD_SIZE
        self.templates = load_templates(templates_dir)

        # Template matching parameters
        self.overlap_threshold = self.DEFAULT_OVERLAP_THRESHOLD
        self.match_threshold = self.DEFAULT_MATCH_THRESHOLD
        self.scale_factors = self.DEFAULT_SCALE_FACTORS

    @benchmark
    def read(self, image: np.ndarray) -> List[ReadedCard]:
        """
        Detect hand cards by directly scanning the entire image with each template
        No preprocessing - templates and image used as-is

        Returns:
            List of ReadedCard objects
        """
        if not self.templates:
            print("No templates loaded!")
            return []

        all_detections = self._find_all_template_matches(image)
        filtered_detections = self._filter_overlapping_detections(all_detections)
        sorted_detections = self._sort_detections_by_position(filtered_detections)

        # Convert to ReadedCard objects
        readed_cards = []
        for i, detection in enumerate(sorted_detections):
            x, y, w, h = detection['bounding_rect']
            card_region = image[y:y + h, x:x + w].copy()

            readed_card = ReadedCard(
                card_index=i,
                card_region=card_region,
                bounding_rect=detection['bounding_rect'],
                center=detection['center'],
                area=w * h,
                template_name=detection['template_name'],
                match_score=detection['match_score'],
                is_valid=True,  # Player cards are considered valid if detected
                scale=detection['scale']
            )
            readed_cards.append(readed_card)

        return readed_cards

    def _find_all_template_matches(self, image: np.ndarray) -> List[Dict]:
        """Find matches for all templates in the image"""
        all_detections = []

        for template_name, template in self.templates.items():
            detections = self._find_single_template_matches(image, template, template_name)
            all_detections.extend(detections)

        return all_detections

    def _find_single_template_matches(self, image: np.ndarray, template: np.ndarray,
                                      template_name: str) -> List[Dict]:
        """Find all matches of a single template in the image at multiple scales"""
        detections = []
        search_image, offset = self._extract_search_region(image)
        template_h, template_w = template.shape[:2]

        for scale in self.scale_factors:
            scale_detections = self._match_template_at_scale(
                search_image, template, template_name, scale,
                template_w, template_h, offset
            )
            detections.extend(scale_detections)

        return detections

    def _match_template_at_scale(self, search_image: np.ndarray, template: np.ndarray,
                                 template_name: str, scale: float, template_w: int,
                                 template_h: int, offset: Tuple[int, int]) -> List[Dict]:
        """Perform template matching at a specific scale"""
        scaled_w = int(template_w * scale)
        scaled_h = int(template_h * scale)

        # Skip if template becomes too small or too large
        if (scaled_w < self.min_card_size or scaled_h < self.min_card_size or
                scaled_w > search_image.shape[1] or scaled_h > search_image.shape[0]):
            return []

        scaled_template = cv2.resize(template, (scaled_w, scaled_h))
        result = cv2.matchTemplate(search_image, scaled_template, cv2.TM_CCOEFF_NORMED)

        # Find all locations where match is above threshold
        locations = np.where(result >= self.match_threshold)
        detections = []

        for y, x in zip(*locations):
            match_score = result[y, x]
            center_x = x + scaled_w // 2
            center_y = y + scaled_h // 2

            detection = {
                'template_name': template_name,
                'match_score': float(match_score),
                'bounding_rect': (x + offset[0], y + offset[1], scaled_w, scaled_h),
                'center': (center_x + offset[0], center_y + offset[1]),
                'scale': scale,
                'template_size': (template_w, template_h),
                'scaled_size': (scaled_w, scaled_h)
            }
            detections.append(detection)

        return detections

    def _extract_search_region(self, image: np.ndarray) -> Tuple[np.ndarray, Tuple[int, int]]:
        """Extract the search region from the image"""
        if self.search_region is None:
            return image, (0, 0)

        height, width = image.shape[:2]
        x1 = int(width * self.search_region[0])
        y1 = int(height * self.search_region[1])
        x2 = int(width * self.search_region[2])
        y2 = int(height * self.search_region[3])

        region = image[y1:y2, x1:x2]
        return region, (x1, y1)

    def _filter_overlapping_detections(self, detections: List[Dict]) -> List[Dict]:
        """Remove overlapping detections, keeping the ones with highest match scores"""
        if not detections:
            return []

        # Sort by match score (highest first)
        detections.sort(key=lambda x: x['match_score'], reverse=True)
        filtered = []

        for detection in detections:
            if not self._overlaps_with_existing(detection, filtered):
                filtered.append(detection)

        return filtered

    def _overlaps_with_existing(self, detection: Dict, accepted_detections: List[Dict]) -> bool:
        """Check if detection overlaps significantly with any already accepted detection"""
        for accepted in accepted_detections:
            overlap = self._calculate_overlap_ratio(detection['bounding_rect'],
                                                    accepted['bounding_rect'])
            if overlap > self.overlap_threshold:
                return True
        return False

    def _calculate_overlap_ratio(self, rect1: Tuple[int, int, int, int],
                                 rect2: Tuple[int, int, int, int]) -> float:
        """Calculate the overlap ratio between two rectangles"""
        x1, y1, w1, h1 = rect1
        x2, y2, w2, h2 = rect2

        # Calculate intersection
        x_overlap = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
        y_overlap = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))

        if x_overlap == 0 or y_overlap == 0:
            return 0.0

        intersection_area = x_overlap * y_overlap
        area1 = w1 * h1
        area2 = w2 * h2
        union_area = area1 + area2 - intersection_area

        return intersection_area / union_area if union_area > 0 else 0.0

    def _sort_detections_by_position(self, detections: List[Dict]) -> List[Dict]:
        """Sort detections by x-coordinate (left to right)"""
        return sorted(detections, key=lambda x: x['center'][0])

    def draw_detected_cards(self, image: np.ndarray, readed_cards: List[ReadedCard]) -> np.ndarray:
        """
        Draw detected cards on the image
        """
        result = image.copy()

        for i, card in enumerate(readed_cards):
            x, y, w, h = card.bounding_rect

            # Draw bounding rectangle
            cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Draw center point
            cv2.circle(result, card.center, 5, (255, 0, 0), -1)

            # Add label with template name and confidence
            label = f"{card.template_name} ({card.match_score:.2f})"
            cv2.putText(result, label, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Add scale info
            scale_info = f"Scale: {card.scale:.1f}"
            cv2.putText(result, scale_info, (x, y + h + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)

        return result

    def get_detection_summary(self, readed_cards: List[ReadedCard]) -> Dict:
        """
        Get summary information about detections
        """
        if not readed_cards:
            return {
                "total": 0,
                "cards": {},
                "average_confidence": 0.0,
                "scales_used": []
            }

        summary = {
            "total": len(readed_cards),
            "cards": {},
            "average_confidence": sum(card.match_score for card in readed_cards) / len(readed_cards),
            "scales_used": sorted(list(set(card.scale for card in readed_cards)))
        }

        # Count each card type
        for card in readed_cards:
            card_name = card.template_name
            if card_name not in summary["cards"]:
                summary["cards"][card_name] = 0
            summary["cards"][card_name] += 1

        return summary


def write_summary(readed_cards, player_card_reader):
    # Get summary
    summary = player_card_reader.get_detection_summary(readed_cards)
    print(f"\nDetection Summary:")
    print(f"Total detections: {summary['total']}")
    print(f"Average confidence: {summary['average_confidence']:.3f}")
    print(f"Scales used: {summary['scales_used']}")
    print(f"Cards found: {summary['cards']}")
    # Print detailed results
    print(f"\nDetailed Results:")
    for i, card in enumerate(readed_cards):
        print(f"  Detection {i + 1}:")
        print(f"    Template: {card.template_name}")
        print(f"    Confidence: {card.match_score:.3f}")
        print(f"    Position: {card.center}")
        print(f"    Size: {card.bounding_rect[2:4]}")
        print(f"    Scale: {card.scale:.1f}")
        print()
    return summary


# 3. Modified TableCardReader - src/table_card_reader.py

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
        extracted_cards = []

        for i, card in enumerate(detected_cards):
            # Extract card region
            card_region = extract_card(image, card)
            extracted_cards.append(card_region)

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
        save_detected_cards(extracted_cards)

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


# 4. Updated CardReader base class - src/card_reader.py

import numpy as np
from typing import List
from src.readed_card import ReadedCard


class CardReader:
    def read(self, image: np.ndarray) -> List[ReadedCard]:
        pass


# 5. Updated main.py

import cv2

from src.player_card_reader import PlayerCardReader, write_summary
from src.table_card_reader import TableCardReader
from src.utils.result_processor import process_results

if __name__ == "__main__":
    # Table card reading
    imagePath = "resources/screenshots/img.png"
    templates_dir = "resources/templates/full_cards"
    image = cv2.imread(imagePath)
    table_card_reader = TableCardReader(template_dir=templates_dir)
    readed_cards = table_card_reader.read(image)

    # Convert ReadedCard objects back to old format for process_results
    old_format_cards = []
    for card in readed_cards:
        old_format_cards.append({
            'contour': card.contour,
            'bounding_rect': card.bounding_rect,
            'rotated_rect': card.rotated_rect,
            'box_points': card.box_points,
            'area': card.area,
            'center': card.center
        })

    process_results(old_format_cards, "table", image=image, detector=table_card_reader)

if __name__ == "__main__":
    # Player card reading
    imagePath = "resources/screenshots/02_Lobby_exe__0_02__0_05_Pot_Limit_Omaha.png"
    templates_dir = "resources/templates/hand_cards/"
    image = cv2.imread(imagePath)
    player_card_reader = PlayerCardReader(templates_dir=templates_dir)

    readed_cards = player_card_reader.read(image)

    # Write summary
    summary = write_summary(readed_cards, player_card_reader)

    # Create visualization
    result_image = player_card_reader.draw_detected_cards(image, readed_cards)

    # Convert to old format for process_results
    old_format_results = {
        'original': image,
        'result_image': result_image,
        'detections': [
            {
                'template_name': card.template_name,
                'match_score': card.match_score,
                'bounding_rect': card.bounding_rect,
                'center': card.center,
                'scale': card.scale,
                'card_region': card.card_region,
                'area': card.area,
                'aspect_ratio': card.bounding_rect[2] / card.bounding_rect[3] if card.bounding_rect[3] > 0 else 0
            } for card in readed_cards
        ],
        'summary': summary
    }

    process_results(old_format_results, "player", debug=True)

# 6. Updated save_utils.py - src/utils/save_utils.py

import os
import cv2
from typing import List
from src.readed_card import ReadedCard


def save_detected_cards(extracted_cards, output_dir="resources/detected_cards"):
    """
    Save each detected card as a separate PNG file

    Args:
        extracted_cards: List of card images (numpy arrays) or ReadedCard objects
        output_dir: Directory to save the card images
    """
    os.makedirs(output_dir, exist_ok=True)

    for i, card in enumerate(extracted_cards):
        # Handle both old format (numpy arrays) and ReadedCard objects
        if isinstance(card, ReadedCard):
            card_image = card.card_region
        else:
            card_image = card

        filename = os.path.join(output_dir, f"table_card_{i + 1}.png")
        cv2.imwrite(filename, card_image)
        print(f"Saved: {filename}")


def save_readed_player_cards(results, output_dir="resources/readed_player_cards"):
    """Save each detected card region - updated to handle both old and new formats"""
    os.makedirs(output_dir, exist_ok=True)

    # Handle both old format (dict with 'detections') and new format (List[ReadedCard])
    if isinstance(results, dict) and 'detections' in results:
        detections = results['detections']
    elif isinstance(results, list):
        detections = results
    else:
        print("Unknown results format")
        return 0

    for i, detection in enumerate(detections):
        if isinstance(detection, ReadedCard):
            card_region = detection.card_region
            template_name = detection.template_name
            confidence = detection.match_score
            scale = detection.scale if detection.scale else 1.0
        else:
            # Old format
            card_region = detection['card_region']
            template_name = detection['template_name']
            confidence = detection['match_score']
            scale = detection['scale']

        filename = os.path.join(output_dir, f"{template_name}_conf{confidence:.2f}_scale{scale:.1f}_{i}.png")
        cv2.imwrite(filename, card_region)
        print(f"Saved: {filename}")

    return len(detections)