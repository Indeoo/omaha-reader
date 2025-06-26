import multiprocessing
from typing import List, Dict, Tuple, Optional
import numpy as np

from src.domain.card_reader import TableReader
from src.utils.benchmark_utils import benchmark
from src.utils.template_matching_utils import (
    find_template_matches_parallel,
    filter_overlapping_detections,
    sort_detections_by_position
)


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
    """
    Detects player positions (like BTN, SB, BB, etc.) in poker table images
    """
    DEFAULT_MATCH_THRESHOLD = 0.99  # Lower threshold for position markers
    DEFAULT_OVERLAP_THRESHOLD = 0.3
    DEFAULT_MIN_POSITION_SIZE = 15
    #DEFAULT_SCALE_FACTORS = [0.8, 0.9, 1.0, 1.1, 1.2]  # More scale variations for positions
    DEFAULT_SCALE_FACTORS = [1.0]  # More scale variations for positions

    def __init__(self, templates: Dict[str, np.ndarray]):
        """
        Initialize position reader with templates

        Args:
            templates: Dictionary of position_name -> template_image
        """
        self.templates = templates
        self.match_threshold = self.DEFAULT_MATCH_THRESHOLD
        self.overlap_threshold = self.DEFAULT_OVERLAP_THRESHOLD
        self.min_position_size = self.DEFAULT_MIN_POSITION_SIZE
        self.scale_factors = self.DEFAULT_SCALE_FACTORS
        self.max_workers = min(4, multiprocessing.cpu_count())

    @benchmark
    def read(self, image: np.ndarray) -> List[DetectedPosition]:
        """
        Detect player positions in the image

        Args:
            image: Input image (poker table screenshot)

        Returns:
            List of DetectedPosition objects
        """
        if not self.templates:
            print("No position templates loaded!")
            return []

        # Find all template matches
        all_detections = find_template_matches_parallel(
            image=image,
            templates=self.templates,
            search_region=None,  # Search entire image for positions
            scale_factors=self.scale_factors,
            match_threshold=self.match_threshold,
            min_card_size=self.min_position_size,
            max_workers=self.max_workers
        )

        # Filter overlapping detections
        filtered_detections = filter_overlapping_detections(
            detections=all_detections,
            overlap_threshold=self.overlap_threshold
        )

        # Convert to DetectedPosition objects
        detected_positions = []
        for detection in filtered_detections:
            position = DetectedPosition(
                position_name=detection['template_name'],
                center=detection['center'],
                bounding_rect=detection['bounding_rect'],
                match_score=detection['match_score']
            )
            detected_positions.append(position)

        # Sort by match score (highest first) for consistent ordering
        detected_positions.sort(key=lambda p: p.match_score, reverse=True)

        return detected_positions
