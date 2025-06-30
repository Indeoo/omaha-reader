from typing import Optional

from src.core.domain.detection_result import DetectionResult
from src.core.domain.game import Game
from .state_repository import GameStateRepository
from ..domain.readed_card import ReadedCard


class GameStateManager:

    def __init__(self):
        self.repository = GameStateRepository()

    def is_new_game(self, window_name: str, player_cards) -> bool:
        existing_game = self.repository.get_by_window(window_name)

        if existing_game is None:
            return True

        current_player_cards_string = ReadedCard.format_cards_simple(player_cards)
        existing_player_cards_string = existing_game.get_player_cards_string()

        return current_player_cards_string != existing_player_cards_string

    def get_latest_results(self) -> dict:
        return self.repository.get_latest_results_dict()

    def get_notification_data(self) -> dict:
        return self.repository.get_notification_data()
