import threading
from typing import Dict, Optional
from datetime import datetime

from src.core.domain.game import Game
from src.core.domain.readed_card import ReadedCard


class GameStateRepository:

    def __init__(self):
        self.games: Dict[str, Game] = {}
        self.last_update: Optional[str] = None
        self._lock = threading.Lock()

    def get_by_window(self, window_name: str) -> Optional[Game]:
        with self._lock:
            return self.games.get(window_name)

    def get_table_cards(self, window_name: str):
        return self.get_by_window(window_name).table_cards

    def start_new_game(self, window_name: str, player_cards=None, table_cards=None, positions=None) -> Game:
        with self._lock:
            new_game = Game(
                player_cards=player_cards or [],
                table_cards=table_cards or [],
                positions=positions or {}
            )

            self.games[window_name] = new_game
            self.last_update = datetime.now().isoformat()

            return new_game

    def update_bids(self, window_name: str, current_bids) -> bool:
        with self._lock:
            game = self.games.get(window_name)

            if game is None:
                return False

            old_bids = game.current_bids.copy()
            game.current_bids = current_bids or {}

            if old_bids != game.current_bids:
                self.last_update = datetime.now().isoformat()
                return True

            return False

    def update_table_cards(self, window_name: str, table_cards) -> bool:
        with self._lock:
            game = self.games.get(window_name)

            if game is None:
                return False

            old_table_cards_string = game.get_table_cards_string()
            game.table_cards = table_cards or []
            new_table_cards_string = game.get_table_cards_string()

            if old_table_cards_string != new_table_cards_string:
                self.last_update = datetime.now().isoformat()
                return True

            return False

    def is_new_game(self, window_name: str, player_cards) -> bool:
        existing_game = self.get_by_window(window_name)

        if existing_game is None:
            return True

        current_player_cards_string = ReadedCard.format_cards_simple(player_cards)
        existing_player_cards_string = existing_game.get_player_cards_string()

        return current_player_cards_string != existing_player_cards_string

    def get_latest_results_dict(self) -> dict:
        with self._lock:
            return {
                'detections': [game.to_dict(window_name) for window_name, game in self.games.items()],
                'last_update': self.last_update
            }

    def get_notification_data(self) -> dict:
        with self._lock:
            return {
                'type': 'detection_update',
                'detections': [game.to_dict(window_name) for window_name, game in self.games.items()],
                'last_update': self.last_update
            }
