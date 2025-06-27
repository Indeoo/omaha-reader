from typing import List, Dict, Tuple
import numpy as np

from src.core.reader.table_reader import TableReader
from src.core.utils.benchmark_utils import benchmark


class DetectedMove:
    """Simple class to represent a detected move option"""

    def __init__(self, move_type: str, center: Tuple[int, int],
                 bounding_rect: Tuple[int, int, int, int], match_score: float):
        self.move_type = move_type
        self.center = center
        self.bounding_rect = bounding_rect
        self.match_score = match_score

    def __repr__(self):
        return f"DetectedMove({self.move_type}, score={self.match_score:.3f}, center={self.center})"


class PlayerMoveReader(TableReader):
    """Detects player move options (Fold, Call, Raise, etc.) in poker table images"""

    # Default configuration for move detection
    DEFAULT_MATCH_THRESHOLD = 0.95  # High threshold for UI elements
    DEFAULT_OVERLAP_THRESHOLD = 0.3
    DEFAULT_MIN_MOVE_SIZE = 20
    DEFAULT_SCALE_FACTORS = [1.0]

    # Search region based on button locations
    # Fold at x=310, y=460, w=50, h=30 with some margin
    # Other buttons are to the right of fold
    # Image size: 784x584
    DEFAULT_SEARCH_REGION = (
        310 / 784 - 0.02,  # left: ~0.376 (with 2% margin)
        460 / 584 - 0.02,  # top: ~0.768 (with 2% margin)
        0.95,  # right: most of the right side
        520 / 584 + 0.02  # bottom: ~0.910 (with 2% margin)
    )

    def __init__(self, templates: Dict[str, np.ndarray]):
        """
        Initialize player move reader

        Args:
            templates: Dictionary of move_type -> template_image
        """
        super().__init__(
            templates=templates,
            search_region=self.DEFAULT_SEARCH_REGION,
            match_threshold=self.DEFAULT_MATCH_THRESHOLD,
            overlap_threshold=self.DEFAULT_OVERLAP_THRESHOLD,
            min_detection_size=self.DEFAULT_MIN_MOVE_SIZE,
            scale_factors=self.DEFAULT_SCALE_FACTORS
        )

    @benchmark
    def read(self, image: np.ndarray) -> List[DetectedMove]:
        """
        Override read method to add benchmark decorator

        Args:
            image: Input image (poker table screenshot)

        Returns:
            List of DetectedMove objects
        """
        return super().read(image)

    def _get_sort_direction(self) -> str:
        """Move options are sorted by x-coordinate (left to right)"""
        return 'x'

    def _convert_to_domain_objects(self, image: np.ndarray, detections: List[Dict]) -> List[DetectedMove]:
        """
        Convert detection dictionaries to DetectedMove objects

        Args:
            image: Original image
            detections: List of detection dictionaries

        Returns:
            List of DetectedMove objects sorted by x-coordinate
        """
        detected_moves = []

        for detection in detections:
            move = DetectedMove(
                move_type=detection['template_name'],
                center=detection['center'],
                bounding_rect=detection['bounding_rect'],
                match_score=detection['match_score']
            )
            detected_moves.append(move)

        return detected_moves