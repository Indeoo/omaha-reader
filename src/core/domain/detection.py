from typing import Tuple


class Detection:
    def __init__(self, name: str, center: Tuple[int, int],
                 bounding_rect: Tuple[int, int, int, int],
                 match_score: float, scale: float = 1.0):
        self.name = name
        self.center = center
        self.bounding_rect = bounding_rect
        self.match_score = match_score
        self.scale = scale

    @property
    def x(self) -> int:
        return self.bounding_rect[0]

    @property
    def y(self) -> int:
        return self.bounding_rect[1]

    @property
    def width(self) -> int:
        return self.bounding_rect[2]

    @property
    def height(self) -> int:
        return self.bounding_rect[3]

    @property
    def template_name(self) -> str:
        return self.name

    @property
    def position_name(self) -> str:
        return self.name

    def format_with_unicode(self) -> str:
        if not self.name or len(self.name) < 2:
            return self.name or "UNKNOWN"

        # Get rank and suit for cards
        rank = self.name[:-1]
        suit = self.name[-1].upper()

        suit_unicode = {
            'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'
        }

        return f"{rank}{suit_unicode.get(suit, suit)}"

    def __repr__(self):
        return f"Detection(name='{self.name}', center={self.center})"

    def __eq__(self, other):
        if not isinstance(other, Detection):
            return False
        return (self.name == other.name and
                abs(self.match_score - other.match_score) < 0.001)
