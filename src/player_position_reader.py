from typing import List, Dict, Tuple, Optional
import numpy as np

from src.domain.card_reader import TableReader
from src.utils.benchmark_utils import benchmark


class DetectedPosition:
    """Simple class to represent a detected position"""

    def __init__(self, position_name: str, center: Tuple[int, int],
                 bounding_rect: Tuple[int, int, int, int], match_score: float):
        self.position_name = position_name
        self.center = center
        self.bounding_rect = bounding_rect
        self.match_score = match_score

    def __repr__(self):
        return f"DetectedPosition({self.position_name}, score={self.match_score:.3f}, center={self.center})"


class PlayerPositionReader(TableReader):
    """Detects player positions (like BTN, SB, BB, etc.) in poker table images"""

    # Default configuration for position detection
    DEFAULT_MATCH_THRESHOLD = 0.99  # Higher threshold for position markers
    DEFAULT_OVERLAP_THRESHOLD = 0.3
    DEFAULT_MIN_POSITION_SIZE = 15
    DEFAULT_SCALE_FACTORS = [1.0]

    def __init__(self, templates: Dict[str, np.ndarray]):
        """
        Initialize position reader

        Args:
            templates: Dictionary of position_name -> template_image
        """
        super().__init__(
            templates=templates,
            search_region=None,  # Search entire image for positions
            match_threshold=self.DEFAULT_MATCH_THRESHOLD,
            overlap_threshold=self.DEFAULT_OVERLAP_THRESHOLD,
            min_detection_size=self.DEFAULT_MIN_POSITION_SIZE,
            scale_factors=self.DEFAULT_SCALE_FACTORS
        )

    @benchmark
    def read(self, image: np.ndarray) -> List[DetectedPosition]:
        """
        Override read method to add benchmark decorator

        Args:
            image: Input image (poker table screenshot)

        Returns:
            List of DetectedPosition objects
        """
        return super().read(image)

    def _get_sort_direction(self) -> str:
        """Positions are sorted by match score instead of position"""
        return 'score'  # Custom sort for positions

    def _sort_detections(self, detections: List[Dict]) -> List[Dict]:
        """Sort positions by match score (highest first) for consistent ordering"""
        return sorted(detections, key=lambda d: d['match_score'], reverse=True)

    def _convert_to_domain_objects(self, image: np.ndarray, detections: List[Dict]) -> List[DetectedPosition]:
        """
        Convert detection dictionaries to DetectedPosition objects

        Args:
            image: Original image
            detections: List of detection dictionaries

        Returns:
            List of DetectedPosition objects sorted by match score
        """
        detected_positions = []

        for detection in detections:
            position = DetectedPosition(
                position_name=detection['template_name'],
                center=detection['center'],
                bounding_rect=detection['bounding_rect'],
                match_score=detection['match_score']
            )
            detected_positions.append(position)

        return detected_positions