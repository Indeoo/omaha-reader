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

    @staticmethod
    def get_suit_unicode(suit: str) -> str:
        """
        Get Unicode symbol for card suit

        Args:
            suit: Single character suit ('S', 'H', 'D', 'C')

        Returns:
            Unicode suit symbol
        """
        suit_unicode = {
            'S': '♠',  # Spades
            'H': '♥',  # Hearts
            'D': '♦',  # Diamonds
            'C': '♣'  # Clubs
        }
        return suit_unicode.get(suit.upper(), suit)

    @staticmethod
    def get_suit_color_class(suit: str) -> str:
        """
        Get CSS color class for card suit (for web display)

        Args:
            suit: Single character suit ('S', 'H', 'D', 'C')

        Returns:
            Color class name
        """
        suit_colors = {
            'S': 'black',  # Spades
            'H': 'red',  # Hearts
            'D': 'blue',  # Diamonds
            'C': 'green'  # Clubs
        }
        return suit_colors.get(suit.upper(), 'black')

    @staticmethod
    def get_suit_ansi_color(suit: str) -> str:
        """
        Get ANSI color code for card suit (for console display)

        Args:
            suit: Single character suit ('S', 'H', 'D', 'C')

        Returns:
            ANSI color code
        """
        suit_colors = {
            'S': '\033[90m',  # Dark Gray for Spades
            'H': '\033[91m',  # Red for Hearts
            'D': '\033[94m',  # Blue for Diamonds
            'C': '\033[92m'  # Green for Clubs
        }
        return suit_colors.get(suit.upper(), '\033[0m')

    def format_with_unicode(self) -> str:
        """
        Format card with Unicode suit symbol

        Returns:
            Formatted string like "4♠", "J♥", "A♣", "10♦"
        """
        if not self.template_name or len(self.template_name) < 2:
            return self.template_name or "UNKNOWN"

        # Get rank and suit
        rank = self.template_name[:-1]
        suit = self.template_name[-1].upper()

        return f"{rank}{self.get_suit_unicode(suit)}"

    def format_with_score(self, include_score: bool = True) -> str:
        """
        Format card with Unicode symbol and optional match score

        Args:
            include_score: Whether to include match score in brackets

        Returns:
            Formatted string like "4♠[0.85]" or just "4♠"
        """
        card_with_unicode = self.format_with_unicode()
        if include_score and self.match_score is not None:
            card_with_unicode += f"[{self.match_score:.2f}]"
        return card_with_unicode

    def format_with_ansi_color(self, include_score: bool = False) -> str:
        """
        Format card with ANSI color codes for console display

        Args:
            include_score: Whether to include match score

        Returns:
            Colored string for console output
        """
        if not self.template_name or len(self.template_name) < 2:
            return self.template_name or "UNKNOWN"

        suit = self.template_name[-1].upper()
        color_code = self.get_suit_ansi_color(suit)
        reset_code = '\033[0m'

        formatted = self.format_with_score(include_score)
        return f"{color_code}{formatted}{reset_code}"

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

    @staticmethod
    def format_cards_simple(cards: List['ReadedCard']) -> str:
        """
        Format a list of ReadedCard objects as simple concatenated template names

        Args:
            cards: List of ReadedCard objects

        Returns:
            Formatted string like "4S6DJH" (just template names concatenated)
        """
        if not cards:
            return ""
        return ''.join(card.template_name for card in cards if card.template_name)

    @staticmethod
    def format_cards_unicode(cards: List['ReadedCard'], include_scores: bool = False) -> str:
        """
        Format a list of ReadedCard objects with Unicode suit symbols

        Args:
            cards: List of ReadedCard objects
            include_scores: Whether to include match scores

        Returns:
            Formatted string like "4♠ 6♦ J♥" or "4♠[0.85] 6♦[0.92] J♥[0.78]"
        """
        if not cards:
            return ""
        return " ".join(card.format_with_score(include_scores) for card in cards)

    @staticmethod
    def format_cards_ansi(cards: List['ReadedCard'], include_scores: bool = False) -> str:
        """
        Format a list of ReadedCard objects with ANSI colors for console

        Args:
            cards: List of ReadedCard objects
            include_scores: Whether to include match scores

        Returns:
            ANSI colored string for console output
        """
        if not cards:
            return ""
        return " ".join(card.format_with_ansi_color(include_scores) for card in cards)

    # Legacy method for backward compatibility
    @staticmethod
    def format_cards(cards: List['ReadedCard'], show_probabilities: bool = True) -> str:
        """
        Legacy format method - returns simple concatenated template names

        Args:
            cards: List of ReadedCard objects
            show_probabilities: Ignored for backward compatibility

        Returns:
            Formatted string like "4S6DJH"
        """
        return ReadedCard.format_cards_simple(cards)

    def __str__(self) -> str:
        """String representation using the summary"""
        return self.get_summary()

    def __repr__(self) -> str:
        """Detailed representation for debugging"""
        return f"ReadedCard(index={self.card_index}, {self.get_detailed_summary()})"