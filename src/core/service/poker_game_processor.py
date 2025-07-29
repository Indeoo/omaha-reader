import traceback

from loguru import logger

from src.core.domain.captured_window import CapturedWindow
from src.core.domain.game_snapshot import GameSnapshot
from src.core.service.game_state_service import GameStateService
from src.core.service.omaha_action_processor import group_moves_by_street
from src.core.service.template_matcher_service import TemplateMatchService
from src.core.utils.bid_detect_utils import detect_bids
from src.core.utils.detect_utils import DetectUtils
from src.core.utils.drawing_utils import save_detection_result


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
        window_name = captured_image.window_name
        cv2_image = captured_image.get_cv2_image()

        detected_player_cards = TemplateMatchService.find_player_cards(cv2_image)
        detected_table_cards = TemplateMatchService.find_table_cards(cv2_image)
        detected_positions = DetectUtils.detect_positions(cv2_image)
        detected_actions = DetectUtils.get_player_actions_detection(cv2_image)
        detected_bids = detect_bids(cv2_image)

        position_actions = self.convert_to_position_actions(detected_actions, detected_positions)

        try:
            moves = group_moves_by_street(position_actions)

            logger.info(moves)
        except Exception as e:
            logger.error("Error while group_moves_by_street")
            traceback.print_exc()

        #is_new_game = self.game_state_service.is_new_game(window_name, detected_player_cards, detected_positions)
        game_snapshot_builder = (GameSnapshot.builder().with_player_cards(detected_player_cards)
                                 .with_table_cards(detected_table_cards)
                                 .with_bids(detected_bids)
                                 .with_positions(detected_positions)
                                 .with_actions(detected_actions)
                                 )

        game_snapshot = game_snapshot_builder.build()

        is_new_street = self.game_state_service.is_new_street(window_name, detected_table_cards)

        self.game_state_service.create_or_update_game(window_name, game_snapshot, True, is_new_street)

        save_detection_result(timestamp_folder, captured_image, game_snapshot)

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

                result[position_name] = [d.name for d in detection_list]

        logger.info(result)

        return result