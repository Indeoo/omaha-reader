import threading
from typing import Dict, Optional, List
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

    def remove_windows(self, window_names: List[str]) -> bool:
        with self._lock:
            removed_any = False
            for window_name in window_names:
                if window_name in self.games:
                    del self.games[window_name]
                    removed_any = True

            if removed_any:
                self.last_update = datetime.now().isoformat()

            return removed_any

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

            old_table_cards = game.table_cards
            game.table_cards = table_cards or []

            if old_table_cards != game.table_cards:
                self.last_update = datetime.now().isoformat()
                return True

            return False

    def is_new_game(self, window_name: str, player_cards) -> bool:
        existing_game = self.get_by_window(window_name)

        if existing_game is None:
            return True

        return player_cards != existing_game.player_cards

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

    def is_new_street(self, table_cards, window_name):
        previous_table_cards = self.get_table_cards(window_name)
        is_new_street = ReadedCard.format_cards_simple(table_cards) != ReadedCard.format_cards_simple(
            previous_table_cards)
        return is_new_street