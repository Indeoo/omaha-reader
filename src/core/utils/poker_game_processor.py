from typing import List, Dict, Optional

import cv2
import pytesseract

from src.core.domain.captured_image import CapturedImage
from src.core.domain.detection_result import DetectionResult
from src.core.domain.readed_card import ReadedCard
from src.core.reader.player_card_reader import PlayerCardReader
from src.core.reader.player_move_reader import PlayerMoveReader
from src.core.reader.player_position_reader import PlayerPositionReader
from src.core.reader.table_card_reader import TableCardReader
from src.core.service.template_registry import TemplateRegistry
from src.core.utils.opencv_utils import coords_to_search_region


class CardDetectionResult:
    def __init__(self, player_cards: List[ReadedCard], table_cards: List[ReadedCard]):
        self.player_cards = player_cards
        self.table_cards = table_cards

    @property
    def has_cards(self) -> bool:
        return bool(self.player_cards or self.table_cards)


class PositionDetectionResult:
    def __init__(self, player_positions: Dict[int, str]):
        self.player_positions = player_positions

    @property
    def has_positions(self) -> bool:
        return bool(self.player_positions)


class MoveDetectionResult:
    def __init__(self, available_moves: List, is_player_turn: bool):
        self.available_moves = available_moves
        self.is_player_turn = is_player_turn


class StakeDetectionResult:
    def __init__(self, stakes: Dict[str, str]):
        self.stakes = stakes


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

    STAKE_POSITIONS = {
        'POSITION6': (562, 310, 45, 20),
        'POSITION5': (572, 207, 40, 25),
        'POSITION4': (450, 165, 45, 15),
        'POSITION3': (185, 215, 45, 15),
        'POSITION2': (195, 310, 45, 15),
        'POSITION1': (386, 334, 45, 15)
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
        if self.template_registry.has_move_templates():
            self._player_move_reader = PlayerMoveReader(self.template_registry.move_templates)

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

    def detect_cards(self, cv2_image) -> CardDetectionResult:
        try:
            player_cards = PlayerCardReader(
                self.template_registry.player_templates,
                PlayerCardReader.DEFAULT_SEARCH_REGION
            ).read(cv2_image)

            table_cards = TableCardReader(self.template_registry.table_templates, None).read(cv2_image)

            return CardDetectionResult(player_cards, table_cards)

        except Exception as e:
            print(f"❌ Error detecting cards: {str(e)}")
            return CardDetectionResult([], [])

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

            return PositionDetectionResult(player_positions)

        except Exception as e:
            print(f"❌ Error detecting positions: {str(e)}")
            return PositionDetectionResult({})

    def detect_moves(self, cv2_image, window_name: str = "") -> MoveDetectionResult:
        if not self._player_move_reader:
            return MoveDetectionResult([], False)

        try:
            detected_moves = self._player_move_reader.read(cv2_image)

            if detected_moves:
                move_types = [move.move_type for move in detected_moves]
                if window_name:
                    print(f"🎯 Player's move detected in {window_name}! Options: {', '.join(move_types)}")
                return MoveDetectionResult(detected_moves, True)
            else:
                if window_name:
                    print(f"⏸️ Not player's move in {window_name} - no action buttons detected")
                return MoveDetectionResult([], False)

        except Exception as e:
            print(f"❌ Error detecting moves: {str(e)}")
            return MoveDetectionResult([], False)

    def detect_stakes(self, captured_image: CapturedImage) -> StakeDetectionResult:
        stakes = {}

        try:
            for position_name, (x, y, w, h) in self.config.STAKE_POSITIONS.items():
                stake = self.detect_single_stake(captured_image, x, y, w, h)
                if stake:
                    stakes[position_name] = stake

            return StakeDetectionResult(stakes)

        except Exception as e:
            print(f"❌ Error detecting stakes: {str(e)}")
            return StakeDetectionResult({})

    def detect_single_stake(self, captured_image: CapturedImage, x: int, y: int, w: int, h: int) -> str:
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
            print(f"❌ Error detecting stake at ({x}, {y}): {str(e)}")
            return ""

    def should_detect_positions(self, cards_result: CardDetectionResult) -> bool:
        return cards_result.has_cards and self.template_registry.has_position_templates()

    def should_detect_moves(self, cards_result: CardDetectionResult) -> bool:
        return bool(cards_result.player_cards) and self.template_registry.has_move_templates()

    def should_detect_stakes(self, cards_result: CardDetectionResult) -> bool:
        return cards_result.has_cards

    def combine_detection_results(self,
                                  captured_image: CapturedImage,
                                  cards_result: CardDetectionResult,
                                  positions_result: Optional[PositionDetectionResult] = None,
                                  moves_result: Optional[MoveDetectionResult] = None,
                                  stakes_result: Optional[StakeDetectionResult] = None) -> DetectionResult:
        player_positions = positions_result.player_positions if positions_result else {}
        is_player_move = moves_result.is_player_turn if moves_result else False

        if stakes_result and stakes_result.stakes:
            print(f"💰 Stakes detected:")
            for position, stake in stakes_result.stakes.items():
                print(f"    {position}: {stake}")

        return DetectionResult(
            window_name=captured_image.window_name,
            filename=captured_image.filename,
            captured_image=captured_image,
            player_cards=cards_result.player_cards,
            table_cards=cards_result.table_cards,
            positions=player_positions,
            is_player_move=is_player_move
        )