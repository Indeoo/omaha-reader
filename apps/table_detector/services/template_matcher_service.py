import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

import numpy as np

from shared.domain.detection import Detection
from table_detector.services.template_registry import TemplateRegistry
from table_detector.utils.template_matching_utils import (
    find_single_template_matches,
    filter_overlapping_detections,
    sort_detections_by_position
)


@dataclass
class MatchConfig:
    search_region: Optional[Tuple[float, float, float, float]] = None
    threshold: float = 0.955
    overlap_threshold: float = 0.3
    min_size: int = 20
    scale_factors: List[float] = None
    sort_by: str = 'x'  # 'x', 'y', 'score'
    max_workers: int = 4

    def __post_init__(self):
        if self.scale_factors is None:
            self.scale_factors = [1.0]
        if self.max_workers <= 0:
            self.max_workers = min(4, multiprocessing.cpu_count())


class TemplateMatchService:
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent
    TEMPLATE_REGISTRY = TemplateRegistry("canada", project_root)

    @staticmethod
    def find_matches(image: np.ndarray, templates: Dict[str, np.ndarray],
                     config: MatchConfig = None) -> List[Detection]:
        if config is None:
            config = MatchConfig()

        if not templates:
            return []

        # Find all template matches in parallel
        all_detections = []

        with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
            futures = []
            for template_name, template in templates.items():
                future = executor.submit(
                    find_single_template_matches,
                    image, template, template_name,
                    config.search_region, config.scale_factors,
                    config.threshold, config.min_size
                )
                futures.append(future)

            for future in futures:
                detections = future.result()
                all_detections.extend(detections)

        # Filter overlapping detections
        filtered = filter_overlapping_detections(all_detections, config.overlap_threshold)

        # Sort detections
        if config.sort_by == 'score':
            sorted_detections = sorted(filtered, key=lambda d: d['match_score'], reverse=True)
        else:
            sorted_detections = sort_detections_by_position(filtered, config.sort_by)

        # Convert to Detection objects
        return [TemplateMatchService._dict_to_detection(d) for d in sorted_detections]

    @staticmethod
    def _dict_to_detection(detection_dict: Dict) -> Detection:
        return Detection(
            name=detection_dict['template_name'],
            center=detection_dict['center'],
            bounding_rect=detection_dict['bounding_rect'],
            match_score=detection_dict['match_score'],
            scale=detection_dict.get('scale', 1.0)
        )

    # Convenience methods for specific use cases
    @staticmethod
    def find_player_cards(image: np.ndarray) -> List[Detection]:
        config = MatchConfig(
            search_region=(0.2, 0.5, 0.8, 0.95),
            threshold=0.955,
            sort_by='x'
        )
        return TemplateMatchService.find_matches(image, TemplateMatchService.TEMPLATE_REGISTRY.player_templates, config)

    @staticmethod
    def find_table_cards(image: np.ndarray) -> List[Detection]:
        config = MatchConfig(
            search_region=None,  # Search entire image
            threshold=0.955,
            sort_by='x'
        )
        return TemplateMatchService.find_matches(image, TemplateMatchService.TEMPLATE_REGISTRY.table_templates, config)

    @staticmethod
    def find_positions(image: np.ndarray, search_region: Tuple[float, float, float, float] = None) -> List[Detection]:
        config = MatchConfig(
            search_region=search_region,
            threshold=0.99,
            min_size=10,
            sort_by='score'
        )
        return TemplateMatchService.find_matches(image, TemplateMatchService.TEMPLATE_REGISTRY.position_templates,
                                                 config)

    @staticmethod
    def find_actions(image: np.ndarray) -> List[Detection]:
        config = MatchConfig(
            search_region=(0.376, 0.768, 0.95, 0.910),  # Action button area
            threshold=0.95,
            min_size=20,
            sort_by='x'
        )
        return TemplateMatchService.find_matches(image, TemplateMatchService.TEMPLATE_REGISTRY.action_templates, config)

    @staticmethod
    def find_jurojin_actions(image: np.ndarray, search_region: Tuple[float, float, float, float]) -> List[Detection]:
        config = MatchConfig(
            search_region=search_region,
            threshold=0.98,
            min_size=20,
            sort_by='x'
        )
        return TemplateMatchService.find_matches(image, TemplateMatchService.TEMPLATE_REGISTRY.jurojin_action_templates, config)