#!/usr/bin/env python3
"""
Shared image processing functions for both main.py and main_web3.py
Refactored to separate concerns and provide granular detection methods
"""
from typing import Dict, Optional, List
import cv2
import pytesseract

from src.core.domain.captured_image import CapturedImage
from src.core.reader.player_card_reader import PlayerCardReader
from src.core.reader.player_position_reader import PlayerPositionReader
from src.core.reader.table_card_reader import TableCardReader
from src.core.reader.player_move_reader import PlayerMoveReader
from src.core.domain.detection_result import DetectionResult
from src.core.domain.readed_card import ReadedCard
from src.core.utils.opencv_utils import load_templates, pil_to_cv2, coords_to_search_region


class CardDetectionResult:
    """Container for card detection results"""

    def __init__(self, player_cards: List[ReadedCard], table_cards: List[ReadedCard]):
        self.player_cards = player_cards
        self.table_cards = table_cards

    @property
    def has_cards(self) -> bool:
        return bool(self.player_cards or self.table_cards)


class PositionDetectionResult:
    """Container for position detection results"""

    def __init__(self, player_positions: Dict[int, str]):
        self.player_positions = player_positions

    @property
    def has_positions(self) -> bool:
        return bool(self.player_positions)


class MoveDetectionResult:
    """Container for move detection results"""

    def __init__(self, available_moves: List, is_player_turn: bool):
        self.available_moves = available_moves
        self.is_player_turn = is_player_turn


class StakeDetectionResult:
    """Container for stake detection results"""

    def __init__(self, stakes: Dict[str, str]):
        self.stakes = stakes


class PokerGameProcessor:
    # Player position coordinates on 784x584 screen
    PLAYER_POSITIONS = {
        1: {'x': 300, 'y': 375, 'w': 40, 'h': 40},  # Main player
        2: {'x': 35, 'y': 330, 'w': 40, 'h': 40},
        3: {'x': 35, 'y': 173, 'w': 40, 'h': 40},
        4: {'x': 297, 'y': 120, 'w': 40, 'h': 40},
        5: {'x': 562, 'y': 168, 'w': 40, 'h': 40},
        6: {'x': 565, 'y': 332, 'w': 40, 'h': 40}
    }

    POSITION_MARGIN = 10  # Pixels to add around each position for detection

    # Stake detection coordinates
    STAKE_POSITIONS = {
        'POSITION6': (562, 310, 45, 20),
        'POSITION5': (572, 207, 40, 25),
        'POSITION4': (450, 165, 45, 15),
        'POSITION3': (185, 215, 45, 15),
        'POSITION2': (195, 310, 45, 15),
        'POSITION1': (386, 334, 45, 15)
    }

    def __init__(
            self,
            player_templates_dir: str = None,
            table_templates_dir: str = None,
            position_templates_dir: str = None,
            move_templates_dir: str = None,
            player_templates: Dict = None,
            table_templates: Dict = None,
            position_templates: Dict = None,
            move_templates: Dict = None,
            save_result_images=True,
            write_detection_files=True,
    ):
        # Load templates from directories if provided
        if player_templates_dir:
            self.player_templates = load_templates(player_templates_dir)
        elif player_templates:
            self.player_templates = player_templates
        else:
            self.player_templates = {}

        if table_templates_dir:
            self.table_templates = load_templates(table_templates_dir)
        elif table_templates:
            self.table_templates = table_templates
        else:
            self.table_templates = {}

        if position_templates_dir:
            self.position_templates = load_templates(position_templates_dir)
        elif position_templates:
            self.position_templates = position_templates
        else:
            self.position_templates = {}

        if move_templates_dir:
            self.move_templates = load_templates(move_templates_dir)
        elif move_templates:
            self.move_templates = move_templates
        else:
            self.move_templates = {}

        self.save_result_images = save_result_images
        self.write_detection_files = write_detection_files

        # Initialize readers
        self._init_readers()

    def _init_readers(self):
        """Initialize all detection readers"""
        # Initialize move reader if templates available
        self._player_move_reader = None
        if self.move_templates:
            self._player_move_reader = PlayerMoveReader(self.move_templates)

        # Initialize position readers for all players
        self._player_position_readers = {}
        self._init_all_player_position_readers()

    def _init_all_player_position_readers(self):
        """Initialize position readers for all 6 player positions"""
        if not self.position_templates:
            return

        try:
            # Create a reader for each player position
            for player_num, coords in self.PLAYER_POSITIONS.items():
                search_region = coords_to_search_region(
                    x=coords['x'] - self.POSITION_MARGIN,
                    y=coords['y'] - self.POSITION_MARGIN,
                    w=coords['w'] + 2 * self.POSITION_MARGIN,
                    h=coords['h'] + 2 * self.POSITION_MARGIN,
                    image_width=784,
                    image_height=584
                )

                reader = PlayerPositionReader(self.position_templates)
                reader.search_region = search_region
                self._player_position_readers[player_num] = reader

                print(f"✅ Player {player_num} position reader initialized with search region: {search_region}")
        except Exception as e:
            print(f"❌ Error initializing player position readers: {str(e)}")

    def detect_cards(self, cv2_image) -> CardDetectionResult:
        """
        Detect player and table cards in the image

        Args:
            cv2_image: OpenCV format image

        Returns:
            CardDetectionResult containing detected cards
        """
        try:
            # Detect player cards
            player_cards = PlayerCardReader(
                self.player_templates,
                PlayerCardReader.DEFAULT_SEARCH_REGION
            ).read(cv2_image)

            # Detect table cards
            table_cards = TableCardReader(self.table_templates, None).read(cv2_image)

            return CardDetectionResult(player_cards, table_cards)

        except Exception as e:
            print(f"❌ Error detecting cards: {str(e)}")
            return CardDetectionResult([], [])

    def detect_positions(self, cv2_image) -> PositionDetectionResult:
        """
        Detect player positions in the image

        Args:
            cv2_image: OpenCV format image

        Returns:
            PositionDetectionResult containing detected positions
        """
        if not self.position_templates or not self._player_position_readers:
            return PositionDetectionResult({})

        try:
            player_positions = {}

            # Check each player position
            for player_num, reader in self._player_position_readers.items():
                try:
                    detected_positions = reader.read(cv2_image)

                    if detected_positions:
                        # Take the highest confidence position
                        best_position = detected_positions[0]  # Already sorted by score
                        player_positions[player_num] = best_position.position_name

                except Exception as e:
                    print(f"❌ Error checking player {player_num} position: {str(e)}")

            return PositionDetectionResult(player_positions)

        except Exception as e:
            print(f"❌ Error detecting positions: {str(e)}")
            return PositionDetectionResult({})

    def detect_moves(self, cv2_image, window_name: str = "") -> MoveDetectionResult:
        """
        Detect available move options for the player

        Args:
            cv2_image: OpenCV format image
            window_name: Name of the window for logging

        Returns:
            MoveDetectionResult containing move information
        """
        if not self._player_move_reader:
            return MoveDetectionResult([], False)

        try:
            # Read move options
            detected_moves = self._player_move_reader.read(cv2_image)

            # Log the result
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
        """
        Detect stakes at all position coordinates

        Args:
            captured_image: CapturedImage object

        Returns:
            StakeDetectionResult containing stake information
        """
        stakes = {}

        try:
            for position_name, (x, y, w, h) in self.STAKE_POSITIONS.items():
                stake = self._detect_single_stake(captured_image, x, y, w, h)
                if stake:  # Only store non-empty stakes
                    stakes[position_name] = stake

            return StakeDetectionResult(stakes)

        except Exception as e:
            print(f"❌ Error detecting stakes: {str(e)}")
            return StakeDetectionResult({})

    def _detect_single_stake(self, captured_image: CapturedImage, x: int, y: int, w: int, h: int) -> str:
        """
        Detect stake amount at specific coordinates

        Args:
            captured_image: CapturedImage object
            x, y, w, h: Coordinates and dimensions of the stake area

        Returns:
            Detected stake as string
        """
        try:
            # Convert to OpenCV format
            cv2_image = pil_to_cv2(captured_image.image)
            gray = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2GRAY)

            # Crop to the bubble ROI
            crop = gray[y: y + h, x: x + w]

            # Binarize (invert so text is white on black)
            _, thresh = cv2.threshold(
                crop, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU
            )

            # Upscale to make the dot thicker
            upscaled = cv2.resize(
                thresh, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC
            )

            # Dilate to merge any broken bits of the dot or digits
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            dilated = cv2.dilate(upscaled, kernel, iterations=1)

            # OCR with a strict whitelist and no dictionaries
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
        """
        Determine if position detection should be performed based on card detection

        Args:
            cards_result: Result from card detection

        Returns:
            True if position detection should be performed
        """
        # Only detect positions if we have cards (active game)
        return cards_result.has_cards and bool(self.position_templates)

    def should_detect_moves(self, cards_result: CardDetectionResult) -> bool:
        """
        Determine if move detection should be performed

        Args:
            cards_result: Result from card detection

        Returns:
            True if move detection should be performed
        """
        # Only detect moves if we have player cards (player is in the game)
        return bool(cards_result.player_cards) and bool(self.move_templates)

    def should_detect_stakes(self, cards_result: CardDetectionResult) -> bool:
        """
        Determine if stake detection should be performed

        Args:
            cards_result: Result from card detection

        Returns:
            True if stake detection should be performed
        """
        # Detect stakes if there's any game activity
        return cards_result.has_cards

    def combine_detection_results(self,
                                  captured_image: CapturedImage,
                                  cards_result: CardDetectionResult,
                                  positions_result: Optional[PositionDetectionResult] = None,
                                  moves_result: Optional[MoveDetectionResult] = None,
                                  stakes_result: Optional[StakeDetectionResult] = None) -> DetectionResult:
        """
        Combine individual detection results into a single DetectionResult

        Args:
            captured_image: Original captured image
            cards_result: Card detection results
            positions_result: Position detection results (optional)
            moves_result: Move detection results (optional)
            stakes_result: Stake detection results (optional)

        Returns:
            Combined DetectionResult object
        """
        # Extract data from results
        player_positions = positions_result.player_positions if positions_result else {}
        is_player_move = moves_result.is_player_turn if moves_result else False

        # Log stakes if detected
        if stakes_result and stakes_result.stakes:
            print(f"💰 Stakes detected:")
            for position, stake in stakes_result.stakes.items():
                print(f"    {position}: {stake}")

        # Create DetectionResult object
        return DetectionResult(
            window_name=captured_image.window_name,
            filename=captured_image.filename,
            captured_image=captured_image,
            player_cards=cards_result.player_cards,
            table_cards=cards_result.table_cards,
            positions=player_positions,
            is_player_move=is_player_move
        )
