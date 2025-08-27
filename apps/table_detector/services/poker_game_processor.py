from table_detector.domain.captured_window import CapturedWindow
from table_detector.services.game_state_service import GameStateService
from table_detector.services.gamesnapshot_service import GameSnapshotService
from table_detector.utils.drawing_utils import save_detection_result


class PokerGameProcessor:

    def __init__(
            self,
            game_state_service: GameStateService,
            save_result_images=True,
            write_detection_files=True,
    ):
        self.game_state_service = game_state_service
        self.save_result_images = save_result_images
        self.write_detection_files = write_detection_files

    def process_and_get_changes(self, captured_image: CapturedWindow, timestamp_folder):
        """Process captured image and return formatted game data for transmission."""
        window_name = captured_image.window_name

        game_snapshot = GameSnapshotService.create_game_snapshot(captured_image.get_cv2_image())
        save_detection_result(timestamp_folder, captured_image, game_snapshot)

        # is_new_game = self.game_state_service.is_new_game(window_name, detected_player_cards, detected_positions)

        is_new_street = self.game_state_service.is_new_street(window_name, game_snapshot.table_cards)

        updated_game = self.game_state_service.create_or_update_game(window_name, game_snapshot, True, is_new_street)

        # Return formatted game data for transmission
        return self.game_state_service._game_to_dict(window_name, updated_game)
