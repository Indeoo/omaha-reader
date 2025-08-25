from typing import Tuple


class DetectedBid:
    def __init__(self, position: int, amount_text: str, bounding_rect: Tuple[int, int, int, int],
                 center: Tuple[int, int]):
        self.position = position
        self.amount_text = amount_text
        self.bounding_rect = bounding_rect
        self.center = center

    @property
    def amount(self) -> float:
        try:
            return float(self.amount_text)
        except (ValueError, TypeError):
            return 0.0

    def __repr__(self):
        return f"DetectedBid(pos={self.position}, amount='{self.amount_text}', center={self.center})"