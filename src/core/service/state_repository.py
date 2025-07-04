import threading
from typing import Dict, Optional, List
from datetime import datetime

from loguru import logger

from src.core.domain.detection_result import GameSnapshot
from src.core.domain.game import Game


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

    def is_new_game(self, window_name: str, player_cards, detected_positions) -> bool:
        existing_game = self.get_by_window(window_name)

        if existing_game is None:
            return True

        is_new_game = player_cards != existing_game.player_cards and detected_positions != existing_game.positions

        logger.info(f"{window_name} new game == {is_new_game}")

        return is_new_game

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
        if game_snapshot.positions is None:
            game = Game(
                player_cards=game_snapshot.player_cards,
                table_cards=game_snapshot.table_cards,
            )
        else:
            game = Game(
                player_cards=game_snapshot.player_cards,
                table_cards=game_snapshot.table_cards,
                positions=game_snapshot.positions.values(),
            )

        self.games[window_name] = game

        return game
