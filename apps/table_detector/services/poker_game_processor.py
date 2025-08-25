import traceback

from loguru import logger

from shared.domain.captured_window import CapturedWindow
from shared.domain.game_snapshot import GameSnapshot
from table_detector.services.game_state_service import GameStateService
from table_detector.services.omaha_action_processor import group_moves_by_street
from table_detector.services.template_matcher_service import TemplateMatchService
from table_detector.utils.detect_utils import DetectUtils
from table_detector.utils.drawing_utils import save_detection_result


class PokerGameProcessor:

    def __init__(
            self,
            game_state_service: GameStateService,
            country="canada",
            save_result_images=True,
            write_detection_files=True,
    ):
        self.game_state_service = game_state_service
        self.save_result_images = save_result_images
        self.write_detection_files = write_detection_files


    def process(self, captured_image: CapturedWindow, timestamp_folder):
        """Process captured image and update game state. Returns None for backward compatibility."""
        window_name = captured_image.window_name

        game_snapshot = self.create_game_snapshot(captured_image, timestamp_folder)

        #is_new_game = self.game_state_service.is_new_game(window_name, detected_player_cards, detected_positions)

        is_new_street = self.game_state_service.is_new_street(window_name, game_snapshot.table_cards)

        self.game_state_service.create_or_update_game(window_name, game_snapshot, True, is_new_street)

    def process_and_get_changes(self, captured_image: CapturedWindow, timestamp_folder):
        """Process captured image and return formatted game data for transmission."""
        window_name = captured_image.window_name

        game_snapshot = self.create_game_snapshot(captured_image, timestamp_folder)

        #is_new_game = self.game_state_service.is_new_game(window_name, detected_player_cards, detected_positions)

        is_new_street = self.game_state_service.is_new_street(window_name, game_snapshot.table_cards)

        updated_game = self.game_state_service.create_or_update_game(window_name, game_snapshot, True, is_new_street)
        
        # Return formatted game data for transmission
        return self.game_state_service._game_to_dict(window_name, updated_game)

    def create_game_snapshot(self, captured_image, timestamp_folder):
        cv2_image = captured_image.get_cv2_image()

        detected_player_cards = TemplateMatchService.find_player_cards(cv2_image)
        detected_table_cards = TemplateMatchService.find_table_cards(cv2_image)
        detected_positions = DetectUtils.detect_positions(cv2_image)
        detected_actions = DetectUtils.get_player_actions_detection(cv2_image)
        detected_bids = None #detect_bids(cv2_image)
        moves = self.get_moves(detected_actions, detected_positions)
        game_snapshot_builder = (GameSnapshot.builder().with_player_cards(detected_player_cards)
                                 .with_table_cards(detected_table_cards)
                                 .with_bids(detected_bids)
                                 .with_positions(detected_positions)
                                 .with_actions(detected_actions)
                                 .with_moves(moves)
                                 )
        game_snapshot = game_snapshot_builder.build()
        save_detection_result(timestamp_folder, captured_image, game_snapshot)
        return game_snapshot

    def get_moves(self, detected_actions, detected_positions):
        position_actions = self.convert_to_position_actions(detected_actions, detected_positions)
        try:
            moves = group_moves_by_street(position_actions)

            logger.info(moves)

            return moves
        except Exception as e:
            logger.error("Error while group_moves_by_street")
            traceback.print_exc()

    def convert_to_position_actions(self, actions, positions):
        result = {}

        for player_id, detection_list in actions.items():
            if player_id in positions:
                position_name = positions[player_id].position_name

                if position_name == 'NO':
                    continue

                if position_name.endswith('_fold'):
                    position_name = position_name[:-5]  # Remove exactly "_fold"
                elif position_name.endswith('_low'):
                    position_name = position_name[:-4]  # Remove exactly "_low"
                elif position_name.endswith('_now'):
                    position_name = position_name[:-4]  # Remove exactly "_now"

                result[position_name] = [d.name for d in detection_list]

        logger.info(result)

        return result