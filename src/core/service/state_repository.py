import threading
from typing import Optional
from datetime import datetime

from src.core.domain.game import Game
from src.core.domain.game_state import GameState


class StateRepository:

    def __init__(self):
        self._current_state = None
        self._lock = threading.Lock()

    def get_current_state(self):
        with self._lock:
            return self._current_state

    def update_state(self, new_state) -> bool:
        with self._lock:
            state_changed = self._current_state != new_state

            if state_changed:
                self._current_state = new_state

            return state_changed

    def update_single_game(self, new_game: Game, timestamp_folder: str) -> tuple[bool, Optional[Game]]:
        with self._lock:
            if self._current_state is None:
                self._current_state = GameState(
                    games=[],
                    last_update=datetime.now().isoformat()
                )

            old_game = self._current_state.find_game_by_window(new_game.window_name)
            updated_state = self._current_state.update_game(new_game)
            updated_state.timestamp = timestamp_folder.split('/')[-1]

            # Check if state actually changed
            has_changed = (
                    old_game is None or
                    new_game.get_player_cards_string() != old_game.get_player_cards_string() or
                    new_game.get_table_cards_string() != old_game.get_table_cards_string() or
                    new_game.get_positions_string() != old_game.get_positions_string()
            )

            if has_changed:
                self._current_state = updated_state

            return has_changed, old_game

    def get_latest_results_dict(self) -> dict:
        current_state = self.get_current_state()
        if current_state:
            return current_state.to_dict()

        return {
            'timestamp': None,
            'detections': [],
            'last_update': None
        }

    def get_notification_data(self) -> dict:
        current_state = self.get_current_state()
        if current_state:
            return {
                'type': 'detection_update',
                'timestamp': current_state.timestamp,
                'detections': [game.to_dict() for game in current_state.games],
                'last_update': current_state.last_update
            }

        return {
            'type': 'detection_update',
            'timestamp': None,
            'detections': [],
            'last_update': None
        }