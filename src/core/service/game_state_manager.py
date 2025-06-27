from typing import Optional

from src.core.domain.detection_result import DetectionResult
from src.core.domain.game import Game
from .state_change_detector import StateChangeDetector
from .state_repository import StateRepository


class GameStateManager:

    def __init__(self):
        self.repository = StateRepository()
        self.change_detector = StateChangeDetector()

    def update_state(self, detection_result: DetectionResult, timestamp_folder: str) -> bool:
        new_game = self._convert_result_to_game(detection_result)

        if not new_game:
            return False

        has_changed, old_game = self.repository.update_single_game(new_game, timestamp_folder)

        if has_changed:
            change_result = self.change_detector.detect_single_game_change(new_game, old_game)
            self.change_detector.log_change(change_result)

            if change_result.old_game is None:
                print(f"  🆕 New table detected: '{new_game.window_name}'")

        return has_changed

    def get_latest_results(self) -> dict:
        return self.repository.get_latest_results_dict()

    def get_notification_data(self) -> dict:
        return self.repository.get_notification_data()

    def remove_game(self, window_name: str) -> bool:
        removed = self.repository.remove_game(window_name)
        if removed:
            print(f"🗑️ Removed game: {window_name}")
        return removed

    def _convert_result_to_game(self, result: DetectionResult) -> Optional[Game]:
        if result.has_cards or result.has_positions:
            return Game(
                window_name=result.window_name,
                player_cards=result.player_cards,
                table_cards=result.table_cards,
                positions=result.positions
            )
        return None