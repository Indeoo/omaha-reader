import threading
from typing import Dict, Optional
from datetime import datetime

from src.core.domain.game import Game


class StateRepository:

    def __init__(self):
        self.games: Dict[str, Game] = {}
        self.previous_game_states: Dict[str, Game] = {}
        self.last_update: Optional[str] = None
        self._lock = threading.Lock()

    def find_game_by_window(self, window_name: str) -> Optional[Game]:
        with self._lock:
            return self.games.get(window_name)

    def update_single_game(self, window_name: str, new_game: Game) -> tuple[bool, Optional[Game]]:
        with self._lock:
            old_game = self.games.get(window_name)
            self.games[window_name] = new_game

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

    def is_empty(self) -> bool:
        with self._lock:
            return len(self.games) == 0

    def remove_game(self, window_name: str):
        with self._lock:
            self.games.pop(window_name, None)
            self.previous_game_states.pop(window_name, None)

    def get_all_window_names(self) -> list[str]:
        with self._lock:
            return list(self.games.keys())