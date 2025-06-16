import multiprocessing
from typing import List, Dict
import numpy as np

from src.domain.card_reader import CardReader
from src.domain.readed_card import ReadedCard
from src.utils.template_matching_utils import (
    find_template_matches_parallel,
    filter_overlapping_detections,
    sort_detections_by_position,
    draw_detected_cards as draw_detections
)


class OmahaCardReader(CardReader):
    DEFAULT_SEARCH_REGION = (0.2, 0.5, 0.8, 0.95)
    #                       (left, top, right, bottom)
    DEFAULT_MIN_CARD_SIZE = 20
    DEFAULT_OVERLAP_THRESHOLD = 0.3
    DEFAULT_MATCH_THRESHOLD = 0.955
    # DEFAULT_SCALE_FACTORS = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    DEFAULT_SCALE_FACTORS = [1.0]

    def __init__(self, templates, search_region=DEFAULT_SEARCH_REGION):
        """
        Template-first detector that scans the entire image directly with templates
        No preprocessing, no assumptions about colors or regions

        Args:
            templates: Dictionary of template_name -> template_image
            search_region: (left, top, right, bottom) as ratios of image size
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

        # Find all template matches using the extracted function
        all_detections = find_template_matches_parallel(
            image=image,
            templates=self.templates,
            search_region=self.search_region,
            scale_factors=self.scale_factors,
            match_threshold=self.match_threshold,
            min_card_size=self.min_card_size,
            max_workers=self.max_workers
        )

        # Filter overlapping detections
        filtered_detections = filter_overlapping_detections(
            detections=all_detections,
            overlap_threshold=self.overlap_threshold
        )

        # Sort detections by position
        sorted_detections = sort_detections_by_position(
            detections=filtered_detections,
            sort_by='x'
        )

        # Convert to ReadedCard objects
        readed_cards = self._convert_to_readed_cards(image, sorted_detections)

        # Sort cards by x-coordinate
        sorted_cards = sorted(readed_cards, key=lambda card: card.center[0])
        return sorted_cards

    def _convert_to_readed_cards(self, image: np.ndarray, detections: List[Dict]) -> List[ReadedCard]:
        """
        Convert detection dictionaries to ReadedCard objects

        Args:
            image: Original image
            detections: List of detection dictionaries

        Returns:
            List of ReadedCard objects
        """
        readed_cards = []

        for i, detection in enumerate(detections):
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

    def draw_detected_cards(self, image: np.ndarray, readed_cards: List[ReadedCard]) -> np.ndarray:
        """
        Draw detected cards on the image

        Args:
            image: Input image
            readed_cards: List of ReadedCard objects

        Returns:
            Image with drawn detections
        """
        # Convert ReadedCard objects back to detection dictionaries
        detections = []
        for card in readed_cards:
            detection = {
                'template_name': card.template_name,
                'match_score': card.match_score,
                'bounding_rect': card.bounding_rect,
                'center': card.center,
                'scale': card.scale
            }
            detections.append(detection)

        # Use the extracted drawing function
        return draw_detections(
            image=image,
            detections=detections,
            color=(0, 255, 0),
            thickness=2,
            font_scale=0.6,
            show_scale=True
        )