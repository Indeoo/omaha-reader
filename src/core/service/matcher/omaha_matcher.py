from abc import ABC, abstractmethod
import multiprocessing
from typing import List, Dict, Tuple, Optional, Any
import numpy as np
from loguru import logger

from src.core.utils.template_matching_utils import (
    find_template_matches_parallel,
    filter_overlapping_detections,
    sort_detections_by_position,
)


class OmahaTableMatcher(ABC):
    """
    Base class for all table-based readers (cards, positions, etc.)
    Contains common template matching logic
    """
    DEFAULT_MATCH_THRESHOLD = 0.99  # Higher threshold for position markers
    DEFAULT_OVERLAP_THRESHOLD = 0.3
    DEFAULT_MIN_POSITION_SIZE = 15
    DEFAULT_SCALE_FACTORS = [1.0]

    def __init__(self,
                 templates: Dict[str, np.ndarray],
                 search_region: Optional[Tuple[float, float, float, float]] = None,
                 match_threshold: float = 0.955,
                 overlap_threshold: float = 0.3,
                 min_detection_size: int = 20,
                 scale_factors: List[float] = None,
                 max_workers: Optional[int] = None):
        """
        Initialize the base reader

        Args:
            templates: Dictionary of template_name -> template_image
            search_region: (left, top, right, bottom) as ratios of image size
            match_threshold: Minimum match score to consider
            overlap_threshold: Maximum allowed overlap ratio for filtering
            min_detection_size: Minimum detection size in pixels
            scale_factors: List of scale factors to try
            max_workers: Maximum number of parallel workers (None for auto)
        """
        self.templates = templates or {}
        self.search_region = search_region
        self.match_threshold = match_threshold
        self.overlap_threshold = overlap_threshold
        self.min_detection_size = min_detection_size
        self.scale_factors = scale_factors or [1.0]
        self.max_workers = max_workers or min(4, multiprocessing.cpu_count())

    def read(self, image: np.ndarray) -> List[Any]:
        if not self.templates:
            logger.error(f"No templates loaded for {self.__class__.__name__}!")
            return []

        # Find all template matches
        detections = self._find_template_matches(image)

        # Filter overlapping detections
        filtered_detections = self._filter_detections(detections)

        # Sort detections
        sorted_detections = self._sort_detections(filtered_detections)

        return self._convert_to_domain_objects(image, sorted_detections)

    def _find_template_matches(self, image: np.ndarray) -> List[Dict]:
        """Find all template matches using parallel execution"""
        return find_template_matches_parallel(
            image=image,
            templates=self.templates,
            search_region=self.search_region,
            scale_factors=self.scale_factors,
            match_threshold=self.match_threshold,
            min_card_size=self.min_detection_size,
            max_workers=self.max_workers
        )

    def _filter_detections(self, detections: List[Dict]) -> List[Dict]:
        """Filter overlapping detections"""
        return filter_overlapping_detections(
            detections=detections,
            overlap_threshold=self.overlap_threshold
        )

    def _sort_detections(self, detections: List[Dict]) -> List[Dict]:
        """Sort detections by position (can be overridden by subclasses)"""
        return sort_detections_by_position(
            detections=detections,
            sort_by=self._get_sort_direction()
        )

    def _get_sort_direction(self) -> str:
        """Get sort direction (can be overridden by subclasses)"""
        return 'x'  # Default: left to right

    @abstractmethod
    def _convert_to_domain_objects(self, image: np.ndarray, detections: List[Dict]) -> List[Any]:
        pass