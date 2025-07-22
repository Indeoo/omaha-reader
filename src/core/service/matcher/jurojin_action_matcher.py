from typing import List, Dict, Any

import numpy as np

from src.core.service.matcher.omaha_matcher import OmahaTableMatcher


class DetectedAction:
    def __init__(self, detected_action, center, bounding_rect, match_score):
        self.detected_action = detected_action
        self.center = center
        self.bounding_rect = bounding_rect
        self.match_score = match_score


class JurojinActionMatcher(OmahaTableMatcher):

    def _convert_to_domain_objects(self, image: np.ndarray, detections: List[Dict]) -> List[Any]:
        detected_moves = []

        for detection in detections:
            move = DetectedAction(
                move_type=detection['template_name'],
                center=detection['center'],
                bounding_rect=detection['bounding_rect'],
                match_score=detection['match_score']
            )
            detected_moves.append(move)

        return detected_moves
