import threading
from typing import Dict, Optional, List
from datetime import datetime

from src.core.domain.game import Game
from src.core.domain.game_snapshot import GameSnapshot


class GameStateRepository:

    def __init__(self):
        self.games: Dict[str, Game] = {}
        self.last_update: Optional[str] = None
        self._lock = threading.Lock()

    def get_by_window(self, window_name: str) -> Optional[Game]:
        with self._lock:
            return self.games.get(window_name)

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

    def get_all(self) -> dict:
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

    def create_by_snapshot(self, window_name: str, game_snapshot: GameSnapshot):
        with self._lock:
            if game_snapshot.positions is None:
                game = Game(
                    player_cards=game_snapshot.player_cards,
                    table_cards=game_snapshot.table_cards,
                )
            else:
                game = Game(
                    player_cards=game_snapshot.player_cards,
                    table_cards=game_snapshot.table_cards,
                    positions=game_snapshot.positions,
                )

            self.games[window_name] = game
            self.last_update = datetime.now().isoformat()

            return game