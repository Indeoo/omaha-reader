from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass

from src.core.domain.game import Game


@dataclass
class GameState:
    timestamp: Optional[str]
    games: List[Game]
    last_update: Optional[str]

    def __init__(self, timestamp: str = None, games: List[Game] = None, last_update: str = None):
        self.timestamp = timestamp
        self.games = games or []
        self.last_update = last_update or datetime.now().isoformat()

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

    def update_game(self, new_game: Game) -> 'GameState':
        updated_games = list(self.games)
        game_index = self.get_game_index(new_game.window_name)

        if game_index is not None:
            updated_games[game_index] = new_game
        else:
            updated_games.append(new_game)

        return GameState(
            timestamp=self.timestamp,
            games=updated_games,
            last_update=datetime.now().isoformat()
        )

    def remove_game(self, window_name: str) -> 'GameState':
        updated_games = [game for game in self.games if game.window_name != window_name]
        return GameState(
            timestamp=self.timestamp,
            games=updated_games,
            last_update=datetime.now().isoformat()
        )

    def to_dict(self) -> dict:
        return {
            'timestamp': self.timestamp,
            'detections': [game.to_dict() for game in self.games],
            'last_update': self.last_update
        }

    def is_empty(self) -> bool:
        return len(self.games) == 0