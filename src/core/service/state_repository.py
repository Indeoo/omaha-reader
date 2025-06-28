import threading
from typing import List, Optional, Dict
from datetime import datetime

from src.core.domain.game import Game


class StateRepository:

    def __init__(self):
        self.games: List[Game] = []
        self.previous_game_states: Dict[str, Game] = {}
        self.last_update: Optional[str] = None
        self._lock = threading.Lock()

    def find_game_by_window(self, window_name: str) -> Optional[Game]:
        for game in self.games:
            if game.window_name == window_name:
                return game
        return None

    def get_game_index(self, window_name: str) -> Optional[int]:
        for i, game in enumerate(self.games):
            if game.window_name == window_name:
                return i
        return None

    def update_single_game(self, new_game: Game) -> tuple[bool, Optional[Game]]:
        with self._lock:
            old_game = self.find_game_by_window(new_game.window_name)
            game_index = self.get_game_index(new_game.window_name)

            if game_index is not None:
                self.games[game_index] = new_game
            else:
                self.games.append(new_game)

            has_changed = (
                old_game is None or
                new_game.get_player_cards_string() != old_game.get_player_cards_string() or
                new_game.get_table_cards_string() != old_game.get_table_cards_string() or
                new_game.get_positions_string() != old_game.get_positions_string()
            )

            if has_changed:
                self.last_update = datetime.now().isoformat()

            return has_changed, old_game

    def get_previous_game_state(self, window_name: str) -> Optional[Game]:
        with self._lock:
            return self.previous_game_states.get(window_name)

    def store_previous_game_state(self, window_name: str, game: Game):
        with self._lock:
            self.previous_game_states[window_name] = game

    def get_latest_results_dict(self) -> dict:
        with self._lock:
            return {
                'detections': [game.to_dict() for game in self.games],
                'last_update': self.last_update
            }

    def get_notification_data(self) -> dict:
        with self._lock:
            return {
                'type': 'detection_update',
                'detections': [game.to_dict() for game in self.games],
                'last_update': self.last_update
            }

    def is_empty(self) -> bool:
        with self._lock:
            return len(self.games) == 0