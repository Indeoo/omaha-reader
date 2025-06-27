from typing import List, Dict, Tuple, Optional
import numpy as np

from src.core.reader.table_reader import TableReader
from src.core.domain.readed_card import ReadedCard


class OmahaCardReader(TableReader):
    """Player card reader for Omaha poker using template matching"""

    # Default configuration for Omaha player cards
    DEFAULT_SEARCH_REGION = (0.2, 0.5, 0.8, 0.95)  # (left, top, right, bottom)
    DEFAULT_MATCH_THRESHOLD = 0.955
    DEFAULT_OVERLAP_THRESHOLD = 0.3
    DEFAULT_MIN_CARD_SIZE = 20
    DEFAULT_SCALE_FACTORS = [1.0]

    def __init__(self,
                 templates: Dict[str, np.ndarray],
                 search_region: Optional[Tuple[float, float, float, float]] = None):
        """
        Initialize Omaha card reader

        Args:
            templates: Dictionary of template_name -> template_image
            search_region: (left, top, right, bottom) as ratios of image size
        """
        super().__init__(
            templates=templates,
            search_region=search_region or self.DEFAULT_SEARCH_REGION,
            match_threshold=self.DEFAULT_MATCH_THRESHOLD,
            overlap_threshold=self.DEFAULT_OVERLAP_THRESHOLD,
            min_detection_size=self.DEFAULT_MIN_CARD_SIZE,
            scale_factors=self.DEFAULT_SCALE_FACTORS
        )

    def _convert_to_domain_objects(self, image: np.ndarray, detections: List[Dict]) -> List[ReadedCard]:
        """
        Convert detection dictionaries to ReadedCard objects

        Args:
            image: Original image
            detections: List of detection dictionaries

        Returns:
            List of ReadedCard objects sorted by x-coordinate
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

        # Sort cards by x-coordinate for consistent ordering
        return sorted(readed_cards, key=lambda card: card.center[0])