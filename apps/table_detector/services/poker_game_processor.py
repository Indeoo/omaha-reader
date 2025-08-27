from typing import List, Dict

from loguru import logger

from table_detector.domain.captured_window import CapturedWindow
from shared.domain.game_snapshot import GameSnapshot
from apps.shared.domain.position import Position
from apps.shared.domain.moves import MoveType
from table_detector.services.game_state_service import GameStateService
from table_detector.services.omaha_action_processor import group_moves_by_street
from table_detector.services.template_matcher_service import TemplateMatchService
from table_detector.utils.detect_utils import DetectUtils
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

        game_snapshot = self.create_game_snapshot(captured_image.get_cv2_image())
        save_detection_result(timestamp_folder, captured_image, game_snapshot)

        # is_new_game = self.game_state_service.is_new_game(window_name, detected_player_cards, detected_positions)

        is_new_street = self.game_state_service.is_new_street(window_name, game_snapshot.table_cards)

        updated_game = self.game_state_service.create_or_update_game(window_name, game_snapshot, True, is_new_street)

        # Return formatted game data for transmission
        return self.game_state_service._game_to_dict(window_name, updated_game)

    def create_game_snapshot(self, cv2_image):
        detected_player_cards = TemplateMatchService.find_player_cards(cv2_image)
        detected_table_cards = TemplateMatchService.find_table_cards(cv2_image)
        detected_positions = DetectUtils.detect_positions(cv2_image)
        detected_actions = DetectUtils.get_player_actions_detection(cv2_image)
        detected_bids = None

        position_actions = self.convert_to_position_actions(detected_actions, detected_positions)
        moves = group_moves_by_street(position_actions)
        logger.info(moves)

        game_snapshot = (
            GameSnapshot
            .builder()
            .with_player_cards(detected_player_cards)
            .with_table_cards(detected_table_cards)
            .with_bids(detected_bids)
            .with_positions(detected_positions)
            .with_actions(detected_actions)
            .with_moves(moves)
            .build()
        )

        return game_snapshot


    def convert_to_position_actions(self, actions, positions) -> Dict[Position, List[MoveType]]:
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

                try:
                    # Convert position string to Position enum
                    position_enum = Position.normalize_position(position_name)

                    # Convert detection names to MoveType enums
                    move_types = []
                    for d in detection_list:
                        try:
                            move_type = MoveType.normalize_action(d.name)
                            move_types.append(move_type)
                        except ValueError as e:
                            logger.warning(f"Skipping invalid move '{d.name}' for position {position_name}: {e}")
                            continue

                    if move_types:  # Only add if we have valid moves
                        result[position_enum] = move_types

                except ValueError as e:
                    logger.warning(f"Skipping invalid position '{position_name}': {e}")
                    continue

        logger.info(result)

        return result
