from typing import Tuple, Optional, List

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

    def get_summary(self) -> str:
        """
        Get a concise summary of the card information

        Returns:
            String summary of the card (e.g., "9H (0.85, scale:1.2)" or "AS (0.92, table)")
        """
        # Start with template name or placeholder
        card_name = self.template_name or "UNKNOWN"

        # Format match score
        score_str = f"{self.match_score:.2f}" if self.match_score is not None else "N/A"

        # Determine card type and add relevant info
        if self.scale is not None:
            # Player card - include scale
            type_info = f"scale:{self.scale:.1f}"
        elif self.contour is not None or self.rotated_rect is not None:
            # Table card - indicate it's a table card
            type_info = "table"
        else:
            # Unknown type
            type_info = "unknown"

        # Add validity indicator if not valid
        validity = "" if self.is_valid else " ❌"

        return f"{card_name} ({score_str}, {type_info}){validity}"

    def get_detailed_summary(self) -> str:
        """
        Get a detailed summary with position and size information

        Returns:
            Detailed string summary
        """
        basic_summary = self.get_summary()

        # Add position and size info
        x, y, w, h = self.bounding_rect
        position_info = f"pos:({self.center[0]},{self.center[1]}), size:{w}x{h}"

        return f"{basic_summary} - {position_info}"

    def format_card_with_unicode(self, card_name: str) -> str:
        """
        Convert card name to include Unicode suit symbols

        Args:
            card_name: Card name like "4S", "JH", "AC", "10D"

        Returns:
            Formatted string like "4S(♤)", "JH(♡)", "AC(♧)", "10D(♢)"
        """
        if not card_name or len(card_name) < 2:
            return card_name

        # Unicode suit symbols mapping
        suit_unicode = {
            'S': '♤',  # Spades (black spade suit)
            'H': '♡',  # Hearts (white heart suit)
            'D': '♢',  # Diamonds (white diamond suit)
            'C': '♧'  # Clubs (white club suit)
        }

        # Get the last character as suit
        suit = card_name[-1].upper()

        if suit in suit_unicode:
            return f"{card_name}({suit_unicode[suit]})"
        else:
            return card_name

    def format_single_card(self, show_probabilities: bool) -> str:
        """
        Format a single ReadedCard with Unicode suit symbol and optional probability

        Args:
            show_probabilities: Whether to include match score/probability in the output

        Returns:
            Formatted string like "4S(♤)[0.85]" or just "4S(♤)"
        """
        card_with_unicode = self.format_card_with_unicode(self.template_name)
        if show_probabilities and self.match_score is not None:
            card_with_unicode += f"[{self.match_score:.2f}]"

        return card_with_unicode

    @staticmethod
    def format_cards(cards: List['ReadedCard'], show_probabilities: bool = True) -> str:
        """
        Format a list of ReadedCard objects with Unicode suit symbols and optionally include probabilities

        Args:
            cards: List of ReadedCard objects
            show_probabilities: Whether to include match scores/probabilities in the output

        Returns:
            Formatted string like "4S6DJH" (just template names concatenated)
        """
        if not cards:
            return ""

        res = ''.join(card.template_name for card in cards if card.template_name)
        return res

    def __str__(self) -> str:
        """String representation using the summary"""
        return self.get_summary()

    def __repr__(self) -> str:
        """Detailed representation for debugging"""
        return f"ReadedCard(index={self.card_index}, {self.get_detailed_summary()})"