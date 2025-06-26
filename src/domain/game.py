from typing import List, Optional
from datetime import datetime


class Game:
    """
    Represents the state of a single Poker game/table.
    """

    def __init__(
            self,
            window_name: str,
            player_cards: List = None,
            table_cards: List = None,
            player_cards_string: str = "",
            table_cards_string: str = ""
    ):
        """
        Initialize a Game instance.

        Args:
            window_name: Name of the window/table
            player_cards: List of player cards with display info
            table_cards: List of table cards with display info
            player_cards_string: Raw string representation of player cards
            table_cards_string: Raw string representation of table cards
        """
        self.window_name = window_name
        self.player_cards = player_cards or []
        self.table_cards = table_cards or []
        self.player_cards_string = player_cards_string
        self.table_cards_string = table_cards_string
        self.timestamp = datetime.now()

    def to_dict(self):
        """Convert Game instance to dictionary for JSON serialization"""
        return {
            'window_name': self.window_name,
            'player_cards': self.player_cards,
            'table_cards': self.table_cards,
            'player_cards_string': self.player_cards_string,
            'table_cards_string': self.table_cards_string
        }