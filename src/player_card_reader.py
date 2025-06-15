import cv2
import numpy as np
from typing import List, Tuple, Dict
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

from src.domain.card_reader import CardReader
from src.domain.readed_card import ReadedCard
from src.utils.benchmark_utils import benchmark
from src.utils.opencv_utils import matchCV2Template


class OmahaCardReader(CardReader):
    DEFAULT_SEARCH_REGION = (0.2, 0.5, 0.8, 0.95)
    #                       (left, top, right, bottom)
    DEFAULT_MIN_CARD_SIZE = 20
    DEFAULT_OVERLAP_THRESHOLD = 0.3
    DEFAULT_MATCH_THRESHOLD = 0.955
    #DEFAULT_SCALE_FACTORS = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    DEFAULT_SCALE_FACTORS = [1.0]

    def __init__(self, templates, search_region = DEFAULT_SEARCH_REGION):
        """
        Template-first detector that scans the entire image directly with templates
        No preprocessing, no assumptions about colors or regions

        Args:
            templates_dir: Directory containing hand card templates
        """
        self.search_region = search_region
        self.min_card_size = self.DEFAULT_MIN_CARD_SIZE
        self.templates = templates

        # Template matching parameters
        self.overlap_threshold = self.DEFAULT_OVERLAP_THRESHOLD
        self.match_threshold = self.DEFAULT_MATCH_THRESHOLD
        self.scale_factors = self.DEFAULT_SCALE_FACTORS

        # Parallel execution parameter
        self.max_workers = min(4, multiprocessing.cpu_count())

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

        # Print all detections with probability > 0
        print(f"\n🔍 ALL DETECTIONS (probability > 0):")
        print("-" * 60)
        detections_above_zero = [d for d in all_detections if d['match_score'] > 0]

        if detections_above_zero:
            # Sort by match score (highest first) for better readability
            detections_above_zero.sort(key=lambda x: x['match_score'], reverse=True)

            for i, detection in enumerate(detections_above_zero, 1):
                print(f"{i:3d}. {detection['template_name']:>6s} | "
                      f"Score: {detection['match_score']:.4f} | "
                      f"Scale: {detection['scale']:.1f} | "
                      f"Center: ({detection['center'][0]:3d}, {detection['center'][1]:3d}) | "
                      f"Size: {detection['scaled_size'][0]:3d}x{detection['scaled_size'][1]:3d}")

            print(f"\nTotal detections above 0: {len(detections_above_zero)}")
            print(
                f"Detections above threshold ({self.match_threshold}): {len([d for d in detections_above_zero if d['match_score'] >= self.match_threshold])}")
        else:
            print("No detections with probability > 0 found")

        print("-" * 60)


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

        sorted_cards = sorted(readed_cards, key=lambda card: card.center[0])
        return [card for card in sorted_cards]

    def _find_all_template_matches(self, image: np.ndarray) -> List[Dict]:
        """Find matches for all templates in the image using parallel execution"""
        all_detections = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all template matching tasks in parallel
            futures = []
            for template_name, template in self.templates.items():
                future = executor.submit(
                    self._find_single_template_matches,
                    image, template, template_name
                )
                futures.append(future)

            # Collect results
            for future in futures:
                detections = future.result()
                all_detections.extend(detections)

        return all_detections


    def _find_single_template_matches(self, image: np.ndarray, template: np.ndarray,
                                      template_name: str) -> List[Dict]:
        """Find all matches of a single template in the image at multiple scales"""
        try:
            detections = []
            search_image, offset = self._extract_search_region(image)
            template_h, template_w = template.shape[:2]

            for scale in self.scale_factors:
                scale_detections = self._match_template_at_scale(
                    search_image, template, template_name, scale,
                    template_w, template_h, offset
                )
                detections.extend(scale_detections)
        except Exception as e:
            print(f"{e} template name: {template_name}")
            raise e

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

        result = matchCV2Template(scaled_h, scaled_w, search_image, template)

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
