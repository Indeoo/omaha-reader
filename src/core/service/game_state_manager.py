from typing import List, Optional

from src.core.domain.detection_result import DetectionResult
from src.core.domain.game import Game
from .state_change_detector import StateChangeDetector
from .state_repository import StateRepository


class GameStateManager:

    def __init__(self):
        self.repository = StateRepository()
        self.change_detector = StateChangeDetector()

    def update_state(self, processed_results: List[DetectionResult], timestamp_folder: str) -> bool:
        new_games = self._convert_results_to_games(processed_results)

        if not new_games:
            return False

        # Handle single game update (incremental processing)
        if len(new_games) == 1:
            return self._handle_single_game_update(new_games[0], timestamp_folder)
        else:
            # Handle batch update
            return self._handle_batch_update(new_games, timestamp_folder)

    def _handle_single_game_update(self, new_game: Game, timestamp_folder: str) -> bool:
        has_changed, old_game = self.repository.update_single_game(new_game, timestamp_folder)

        if has_changed:
            change_result = self.change_detector.detect_single_game_change(new_game, old_game)
            self.change_detector.log_change(change_result)

            if change_result.old_game is None:
                print(f"  🆕 New table detected: '{new_game.window_name}'")

        return has_changed

    def _handle_batch_update(self, new_games: List[Game], timestamp_folder: str) -> bool:
        current_state = self.repository.get_current_state()
        old_games = current_state.games if current_state else []

        has_changed = self.change_detector.detect_batch_changes(new_games, old_games)

        if has_changed:
            self.repository.update_batch_games(new_games, timestamp_folder)

        return has_changed

    def get_latest_results(self) -> dict:
        return self.repository.get_latest_results_dict()

    def get_notification_data(self) -> dict:
        return self.repository.get_notification_data()

    def find_game(self, window_name: str) -> Optional[Game]:
        return self.repository.find_game(window_name)

    def remove_game(self, window_name: str) -> bool:
        removed = self.repository.remove_game(window_name)
        if removed:
            print(f"🗑️ Removed game: {window_name}")
        return removed

    def clear_state(self):
        self.repository.clear_state()
        print("🗑️ Game state cleared")

    def _convert_results_to_games(self, processed_results: List[DetectionResult]) -> List[Game]:
        games = []
        for result in processed_results:
            game = self._convert_result_to_game(result)
            if game:
                games.append(game)
        return games

    def _convert_result_to_game(self, result: DetectionResult) -> Optional[Game]:
        if result.has_cards or result.has_positions:
            return Game(
                window_name=result.window_name,
                player_cards=result.player_cards,
                table_cards=result.table_cards,
                positions=result.positions
            )
        return None

    # Legacy compatibility methods
    def is_new_game(self, new_game: Game, old_game: Optional[Game]) -> bool:
        return self.change_detector._is_new_game(new_game, old_game) if old_game else True

    def is_new_street(self, new_game: Game, old_game: Optional[Game]) -> bool:
        return self.change_detector._is_new_street(new_game, old_game) if old_game else False