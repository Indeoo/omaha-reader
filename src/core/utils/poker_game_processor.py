from typing import List, Dict

from src.core.domain.captured_window import CapturedWindow
from src.core.domain.detection_result import DetectionResult
from src.core.domain.readed_card import ReadedCard
from src.core.service.matcher.player_action_matcher import PlayerActionMatcher
from src.core.service.matcher.player_card_matcher import PlayerCardMatcher
from src.core.service.matcher.player_position_matcher import PlayerPositionMatcher, DetectedPosition
from src.core.service.matcher.table_card_matcher import OmahaTableCard
from src.core.service.move_reconstructor import MoveReconstructor
from src.core.service.state_repository import GameStateRepository
from src.core.service.template_registry import TemplateRegistry
from src.core.utils.bid_detect_utils import detect_bids
from src.core.utils.detect_utils import save_detection_result_image
from src.core.utils.fs_utils import write_dict
from src.core.utils.opencv_utils import coords_to_search_region


class ActionDetectionResult:
    def __init__(self, available_moves: List, is_player_turn: bool):
        self.available_moves = available_moves
        self.is_player_turn = is_player_turn


PLAYER_POSITIONS = {
    1: {'x': 300, 'y': 375, 'w': 40, 'h': 40},
    2: {'x': 35, 'y': 330, 'w': 40, 'h': 40},
    3: {'x': 35, 'y': 173, 'w': 40, 'h': 40},
    4: {'x': 297, 'y': 120, 'w': 40, 'h': 40},
    5: {'x': 562, 'y': 168, 'w': 40, 'h': 40},
    6: {'x': 565, 'y': 332, 'w': 40, 'h': 40}
}

POSITION_MARGIN = 10

IMAGE_WIDTH = 784
IMAGE_HEIGHT = 584


class PokerGameProcessor:

    def __init__(
            self,
            state_repository: GameStateRepository,
            country: str = "canada",
            project_root: str = None,
            save_result_images=True,
            write_detection_files=True,
    ):
        self.state_repository = state_repository
        self.save_result_images = save_result_images
        self.write_detection_files = write_detection_files
        self.move_reconstructor = MoveReconstructor()

        self.template_registry = TemplateRegistry(country, project_root)
        self._init_readers()

    def _init_readers(self):
        self._player_move_reader = None
        self._player_move_reader = PlayerActionMatcher(self.template_registry.action_templates)
        self._player_position_readers = {}
        self._init_all_player_position_readers()

    def _init_all_player_position_readers(self):
        if not self.template_registry.has_position_templates():
            return

        try:
            for player_num, coords in PLAYER_POSITIONS.items():
                search_region = coords_to_search_region(
                    x=coords['x'] - POSITION_MARGIN,
                    y=coords['y'] - POSITION_MARGIN,
                    w=coords['w'] + 2 * POSITION_MARGIN,
                    h=coords['h'] + 2 * POSITION_MARGIN,
                    image_width=IMAGE_WIDTH,
                    image_height=IMAGE_HEIGHT
                )

                reader = PlayerPositionMatcher(self.template_registry.position_templates)
                reader.search_region = search_region
                self._player_position_readers[player_num] = reader

                print(f"✅ Player {player_num} position reader initialized with search region: {search_region}")
        except Exception as e:
            print(f"❌ Error initializing player position readers: {str(e)}")

    def process_window(self, captured_image: CapturedWindow, timestamp_folder):
        window_name = captured_image.window_name
        cv2_image = captured_image.get_cv2_image()

        player_cards = self.detect_player_cards(cv2_image)
        is_new_game = self.state_repository.is_new_game(window_name, player_cards)
        table_cards = self.detect_table_cards(cv2_image)

        positions_result = None
        is_new_street = False

        if is_new_game:
            positions_result = self.detect_positions(cv2_image)

            print(f"    ✅ Found positions:")
            for i, position_result in enumerate(positions_result, 1):
                player_num = i
                position = position_result.position_name
                position_type = f"Player {player_num}"
                print(f"        {position_type}: {position}")

            self.state_repository.start_new_game(
                window_name,
                player_cards,
                table_cards,
                positions_result
            )
        else:
            is_new_street = self.state_repository.is_new_street(table_cards, window_name)
            if is_new_street:
                self.state_repository.update_table_cards(window_name, table_cards)

        is_player_move = self.is_player_move(cv2_image, window_name)

        if is_player_move:
            current_game = self.state_repository.get_by_window(window_name)
            bids_before_update = current_game.current_bids

            bids = detect_bids(captured_image)
            write_dict(bids, timestamp_folder, captured_image.filename)
            bids_updated = self.state_repository.update_bids(window_name, bids)

            if bids_updated:
                print(f"💰 Bids updated for {window_name} - reconstructing moves...")
                self.move_reconstructor.process_bid(current_game, bids_before_update, bids)

        if is_new_game or is_player_move or is_new_street:
            result = DetectionResult(
                player_cards,
                table_cards,
                positions_result,
                is_player_move,
            )

            save_detection_result_image(timestamp_folder, captured_image, result)

    def detect_player_cards(self, cv2_image) -> List[ReadedCard]:
        player_cards = PlayerCardMatcher(
            self.template_registry.player_templates,
            PlayerCardMatcher.DEFAULT_SEARCH_REGION
        ).read(cv2_image)

        return player_cards

    def detect_table_cards(self, cv2_image) -> List[ReadedCard]:
        return OmahaTableCard(self.template_registry.table_templates, None).read(cv2_image)

    def detect_positions(self, cv2_image) -> List[DetectedPosition]:
        if not self.template_registry.has_position_templates() or not self._player_position_readers:
            return []

        try:
            player_positions = []

            for player_num, reader in self._player_position_readers.items():
                try:
                    detected_position = reader.read(cv2_image)

                    if detected_position:
                        best_position = detected_position[0]
                        player_positions.append(best_position)

                except Exception as e:
                    print(f"❌ Error checking player {player_num} position: {str(e)}")

            return player_positions

        except Exception as e:
            print(f"❌ Error detecting positions: {str(e)}")
            return []

    def detect_actions(self, cv2_image, window_name: str = "") -> ActionDetectionResult:
        if not self._player_move_reader:
            return ActionDetectionResult([], False)

        try:
            detected_moves = self._player_move_reader.read(cv2_image)

            if detected_moves:
                move_types = [move.move_type for move in detected_moves]
                if window_name:
                    print(f"🎯 Player's move detected in {window_name}! Options: {', '.join(move_types)}")
                return ActionDetectionResult(detected_moves, True)
            else:
                if window_name:
                    print(f"⏸️ Not player's move in {window_name} - no action buttons detected")
                return ActionDetectionResult([], False)

        except Exception as e:
            print(f"❌ Error detecting moves: {str(e)}")
            return ActionDetectionResult([], False)

    def is_player_move(self, cv2_image, window_name) -> bool:
        return len(self.detect_actions(cv2_image, window_name).available_moves) > 0
