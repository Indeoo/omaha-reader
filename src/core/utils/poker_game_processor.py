from typing import List, Dict, Optional

import cv2
import pytesseract

from src.core.domain.captured_image import CapturedWindow
from src.core.domain.detection_result import DetectionResult
from src.core.domain.readed_card import ReadedCard
from src.core.reader.player_card_reader import PlayerCardReader
from src.core.reader.player_move_reader import PlayerActionReader
from src.core.reader.player_position_reader import PlayerPositionReader
from src.core.reader.table_card_reader import TableCardReader
from src.core.service.template_registry import TemplateRegistry
from src.core.utils.opencv_utils import coords_to_search_region


class PositionDetectionResult:
    def __init__(self, player_positions: Dict[int, str]):
        self.player_positions = player_positions

    @property
    def has_positions(self) -> bool:
        return bool(self.player_positions)


class ActionDetectionResult:
    def __init__(self, available_moves: List, is_player_turn: bool):
        self.available_moves = available_moves
        self.is_player_turn = is_player_turn


class BidDetectionResult:
    def __init__(self, bids: Dict[str, str]):
        self.bids = bids


class GameConfiguration:
    PLAYER_POSITIONS = {
        1: {'x': 300, 'y': 375, 'w': 40, 'h': 40},
        2: {'x': 35, 'y': 330, 'w': 40, 'h': 40},
        3: {'x': 35, 'y': 173, 'w': 40, 'h': 40},
        4: {'x': 297, 'y': 120, 'w': 40, 'h': 40},
        5: {'x': 562, 'y': 168, 'w': 40, 'h': 40},
        6: {'x': 565, 'y': 332, 'w': 40, 'h': 40}
    }

    POSITION_MARGIN = 10

    BIDS_POSITIONS = {
        1: (388, 334, 45, 15),
        2: (195, 310, 45, 15),
        3: (185, 215, 45, 15),
        4: (450, 165, 45, 15),
        5: (572, 207, 40, 25),
        6: (562, 310, 45, 20),
    }

    IMAGE_WIDTH = 784
    IMAGE_HEIGHT = 584


class PokerGameProcessor:
    def __init__(
            self,
            country: str = "canada",
            project_root: str = None,
            save_result_images=True,
            write_detection_files=True,
    ):
        self.save_result_images = save_result_images
        self.write_detection_files = write_detection_files
        self.config = GameConfiguration()

        self.template_registry = TemplateRegistry(country, project_root)
        self._init_readers()

    def _init_readers(self):
        self._player_move_reader = None
        #if self.template_registry.has_action_templates():
        self._player_move_reader = PlayerActionReader(self.template_registry.action_templates)
        self._player_position_readers = {}
        self._init_all_player_position_readers()

    def _init_all_player_position_readers(self):
        if not self.template_registry.has_position_templates():
            return

        try:
            for player_num, coords in self.config.PLAYER_POSITIONS.items():
                search_region = coords_to_search_region(
                    x=coords['x'] - self.config.POSITION_MARGIN,
                    y=coords['y'] - self.config.POSITION_MARGIN,
                    w=coords['w'] + 2 * self.config.POSITION_MARGIN,
                    h=coords['h'] + 2 * self.config.POSITION_MARGIN,
                    image_width=self.config.IMAGE_WIDTH,
                    image_height=self.config.IMAGE_HEIGHT
                )

                reader = PlayerPositionReader(self.template_registry.position_templates)
                reader.search_region = search_region
                self._player_position_readers[player_num] = reader

                print(f"✅ Player {player_num} position reader initialized with search region: {search_region}")
        except Exception as e:
            print(f"❌ Error initializing player position readers: {str(e)}")

    def detect_player_cards(self, cv2_image) -> List[ReadedCard]:
        player_cards = PlayerCardReader(
            self.template_registry.player_templates,
            PlayerCardReader.DEFAULT_SEARCH_REGION
        ).read(cv2_image)

        return player_cards

    def detect_table_cards(self, cv2_image) -> List[ReadedCard]:
        return TableCardReader(self.template_registry.table_templates, None).read(cv2_image)

    def detect_positions(self, cv2_image) -> PositionDetectionResult:
        if not self.template_registry.has_position_templates() or not self._player_position_readers:
            return PositionDetectionResult({})

        try:
            player_positions = {}

            for player_num, reader in self._player_position_readers.items():
                try:
                    detected_positions = reader.read(cv2_image)

                    if detected_positions:
                        best_position = detected_positions[0]
                        player_positions[player_num] = best_position.position_name

                except Exception as e:
                    print(f"❌ Error checking player {player_num} position: {str(e)}")

            print(f"    ✅ Found positions:")
            for player_num, position in sorted(player_positions.items()):
                position_type = f"Player {player_num}"
                print(f"        {position_type}: {position}")

            return PositionDetectionResult(player_positions)

        except Exception as e:
            print(f"❌ Error detecting positions: {str(e)}")
            return PositionDetectionResult({})

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

    def detect_bids(self, captured_image: CapturedWindow) -> BidDetectionResult:
        bids = {}

        try:
            for position_name, (x, y, w, h) in self.config.BIDS_POSITIONS.items():
                bid = self.detect_single_bid(captured_image, x, y, w, h)
                if bid:
                    bids[position_name] = float(bid)

            return BidDetectionResult(bids)

        except Exception as e:
            print(f"❌ Error detecting bids: {str(e)}")
            return BidDetectionResult({})

    def detect_single_bid(self, captured_image: CapturedWindow, x: int, y: int, w: int, h: int) -> str:
        try:
            cv2_image = captured_image.get_cv2_image()
            gray = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2GRAY)

            crop = gray[y: y + h, x: x + w]

            _, thresh = cv2.threshold(
                crop, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU
            )

            upscaled = cv2.resize(
                thresh, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC
            )

            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            dilated = cv2.dilate(upscaled, kernel, iterations=1)

            config = (
                "--psm 7 --oem 3 "
                "-c tessedit_char_whitelist=0123456789. "
                "-c load_system_dawg=0 -c load_freq_dawg=0"
            )
            text = pytesseract.image_to_string(dilated, config=config).strip()

            return text

        except Exception as e:
            print(f"❌ Error detecting bids at ({x}, {y}): {str(e)}")
            return ""

    # def should_detect_positions(self, cards_result: CardDetectionResult) -> bool:
    #     return cards_result.has_cards and self.template_registry.has_position_templates()

    # def should_detect_moves(self, cards_result: CardDetectionResult) -> bool:
    #     return bool(cards_result.player_cards) and self.template_registry.has_move_templates()

    def should_detect_bids(self, player_cards: List[ReadedCard]) -> bool:
        return len(player_cards) > 0

    def combine_detection_results(self,
                                  captured_image: CapturedWindow,
                                  player_cards: List[ReadedCard],
                                  table_cards: List[ReadedCard],
                                  positions_result: Optional[PositionDetectionResult] = None,
                                  action_detection_result: Optional[ActionDetectionResult] = None,
                                  bids_result: Optional[BidDetectionResult] = None) -> DetectionResult:
        player_positions = positions_result.player_positions if positions_result else {}
        is_player_turn = action_detection_result.is_player_turn if action_detection_result else False

        if bids_result and bids_result.bids:
            print(f"💰 Bids detected:")
            for position, bid in bids_result.bids.items():
                print(f"    {position}: {bid}")

        return DetectionResult(
            window_name=captured_image.window_name,
            filename=captured_image.filename,
            captured_image=captured_image,
            player_cards=player_cards,
            table_cards=table_cards,
            positions=player_positions,
            is_player_move=is_player_turn
        )
