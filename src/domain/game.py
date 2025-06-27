from typing import List, Optional, Dict
from datetime import datetime
from src.domain.readed_card import ReadedCard


class Game:
    """
    Represents the state of a single Poker game/table.
    """

    def __init__(
            self,
            window_name: str,
            player_cards: List[ReadedCard] = None,
            table_cards: List[ReadedCard] = None
    ):
        """
        Initialize a Game instance.

        Args:
            window_name: Name of the window/table
            player_cards: List of ReadedCard objects for player cards
            table_cards: List of ReadedCard objects for table cards
        """
        self.window_name = window_name
        self.player_cards = player_cards or []
        self.table_cards = table_cards or []
        self.timestamp = datetime.now()

    def get_player_cards_string(self) -> str:
        """Get formatted string of player cards (simple template names)"""
        return ReadedCard.format_cards_simple(self.player_cards)

    def get_table_cards_string(self) -> str:
        """Get formatted string of table cards (simple template names)"""
        return ReadedCard.format_cards_simple(self.table_cards)

    def get_player_cards_for_web(self) -> List[Dict]:
        """Format player cards for web display with suit symbols"""
        return self._format_cards_for_web(self.player_cards)

    def get_table_cards_for_web(self) -> List[Dict]:
        """Format table cards for web display with suit symbols"""
        return self._format_cards_for_web(self.table_cards)

    def _format_cards_for_web(self, cards: List[ReadedCard]) -> List[Dict]:
        """Format cards for web display with suit symbols"""
        if not cards:
            return []

        formatted = []
        for card in cards:
            if card.template_name:
                formatted.append({
                    'name': card.template_name,
                    'display': card.format_with_unicode(),
                    'score': round(card.match_score, 3) if card.match_score else 0
                })
        return formatted

    def has_cards(self) -> bool:
        """Check if any cards were detected"""
        return bool(self.player_cards or self.table_cards)

    def to_dict(self):
        """Convert Game instance to dictionary for JSON serialization"""
        return {
            'window_name': self.window_name,
            'player_cards': self.get_player_cards_for_web(),
            'table_cards': self.get_table_cards_for_web(),
            'player_cards_string': self.get_player_cards_string(),
            'table_cards_string': self.get_table_cards_string()
        }