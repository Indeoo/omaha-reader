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

