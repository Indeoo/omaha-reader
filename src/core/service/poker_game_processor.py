from loguru import logger

from src.core.domain.captured_window import CapturedWindow
from src.core.domain.game_snapshot import GameSnapshot
from src.core.service.action_service import get_player_actions_detection
from src.core.service.game_state_service import GameStateService
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

        detected_actions = DetectUtils.detect_actions(cv2_image, window_name)
        is_player_move = self.game_state_service.is_player_move(detected_actions)

        if not is_player_move:
            self.game_state_service.update_user_cards(captured_image, cv2_image, timestamp_folder, window_name)
            return

        detected_player_cards = TemplateMatchService.find_player_cards(cv2_image)
        detected_table_cards = TemplateMatchService.find_table_cards(cv2_image)
        detected_positions = DetectUtils.detect_positions(cv2_image)
        detected_actions = get_player_actions_detection(cv2_image)

        is_new_game = self.game_state_service.is_new_game(window_name, detected_player_cards, detected_positions)

        detected_bids = detect_bids(cv2_image)

        game_snapshot_builder = (GameSnapshot.builder().with_player_cards(detected_player_cards)
                                 .with_table_cards(detected_table_cards)
                                 .with_bids(detected_bids)
                                 .with_positions(detected_positions)
                                 .with_actions(detected_actions)
                                 )

        game_snapshot = game_snapshot_builder.build()

        is_new_street = self.game_state_service.is_new_street(window_name, game_snapshot)

        #current_game = self.game_state_service.create_or_update_game(window_name, game_snapshot, is_new_game, is_new_street)

        # if is_new_game:
        #     logger.info("New game detected")
        #     self.move_reconstructor.process_bid(current_game, {}, detected_bids)
        # else:
        #     if is_new_street:
        #         logger.info("New street detected")
        #         previous_bids = {}
        #     else:
        #         previous_bids = current_game.get_total_bids_for_street(current_game.get_street())
        #
        #     self.move_reconstructor.process_bid(current_game, previous_bids, detected_bids)

        save_detection_result(timestamp_folder, captured_image, game_snapshot)

    def update_user_cards(self, captured_image, cv2_image, timestamp_folder, window_name):
        logger.info("Not player's move, only update user cards")
        detected_player_cards = TemplateMatchService.find_player_cards(cv2_image)
        game_snapshot = GameSnapshot.builder().with_player_cards(detected_player_cards).build()
        self.game_state_service.create_or_update_game(window_name, game_snapshot, False, False)
        save_detection_result(timestamp_folder, captured_image, game_snapshot)