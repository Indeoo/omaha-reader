from typing import Optional

from src.core.domain.detection_result import DetectionResult
from src.core.domain.game import Game
from .state_change_detector import StateChangeDetector
from .state_repository import StateRepository
from ..domain.readed_card import ReadedCard


class GameStateManager:

    def __init__(self):
        self.repository = StateRepository()
        self.change_detector = StateChangeDetector()

    def manage(self, detection_result: DetectionResult):
        new_game = self._convert_result_to_game(detection_result)

        if not new_game:
            return False

        window_name = detection_result.window_name
        has_changed, old_game = self.repository.update_single_game(window_name, new_game)

        if has_changed:
            change_result = self.change_detector.detect_single_game_change(new_game, old_game)
            self.change_detector.log_change(change_result, window_name)

            if change_result.old_game is None:
                print(f"  🆕 New table detected: '{window_name}'")

    def is_new_game(self, window_name: str, player_cards) -> bool:
        existing_game = self.repository.find_game_by_window(window_name)

        if existing_game is None:
            return True

        current_player_cards_string = ReadedCard.format_cards_simple(player_cards)
        existing_player_cards_string = existing_game.get_player_cards_string()

        return current_player_cards_string != existing_player_cards_string

    def get_previous_game_state(self, window_name: str) -> Optional[Game]:
        return self.repository.get_previous_game_state(window_name)

    def store_previous_game_state(self, window_name: str, game: Game):
        self.repository.store_previous_game_state(window_name, game)

    def get_latest_results(self) -> dict:
        return self.repository.get_latest_results_dict()

    def get_notification_data(self) -> dict:
        return self.repository.get_notification_data()

    def _convert_result_to_game(self, result: DetectionResult) -> Optional[Game]:
        if result.has_cards or result.has_positions:
            return Game(
                player_cards=result.player_cards,
                table_cards=result.table_cards,
                positions=result.positions
            )
        return None