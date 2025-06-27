#!/usr/bin/env python3
"""
Shared image processing functions for both main.py and main_web3.py
"""
from typing import Dict, Callable


from src.core.domain.captured_image import CapturedImage
from src.core.reader.player_card_reader import PlayerCardReader
from src.core.reader.player_position_reader import PlayerPositionReader
from src.core.reader.table_card_reader import TableCardReader
from src.core.reader.player_move_reader import PlayerMoveReader
from src.core.utils.benchmark_utils import benchmark
from src.core.utils.detect_utils import save_detection_result_image
from src.core.domain.detection_result import DetectionResult
from src.core.utils.result_utils import print_detection_result, write_combined_result
from src.core.utils.opencv_utils import load_templates, pil_to_cv2, coords_to_search_region
import cv2
import pytesseract

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
            detect_positions: bool = True,
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

        self.detect_positions = detect_positions
        self.save_result_images = save_result_images
        self.write_detection_files = write_detection_files

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

    def _check_all_player_positions(self, cv2_image) -> Dict[int, str]:
        """
        Check all player positions in the image

        Args:
            cv2_image: OpenCV format image

        Returns:
            Dictionary mapping player number to position name (e.g., {1: 'BTN', 3: 'SB', 4: 'BB'})
        """
        player_positions = {}

        if not self._player_position_readers:
            return player_positions

        try:
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

            return player_positions

        except Exception as e:
            print(f"❌ Error checking player positions: {str(e)}")
            return player_positions

    def process_single_image_public(
            self,
            captured_image: CapturedImage,
            index: int,
            timestamp_folder: str,
            process_callback: Callable = None
    ) -> DetectionResult:
        """
        Public method to process a single image

        Args:
            captured_image: CapturedImage object
            index: Image index
            timestamp_folder: Folder to save results
            process_callback: Optional callback function

        Returns:
            DetectionResult object
        """
        return self._process_single_image(
            captured_image=captured_image,
            index=index,
            process_callback=process_callback,
            timestamp_folder=timestamp_folder
        )

    @benchmark
    def _process_single_image(
            self,
            captured_image: CapturedImage,
            index: int,
            process_callback: Callable,
            timestamp_folder: str
    ) -> DetectionResult:
        """
        Process a single captured image

        Args:
            captured_image: CapturedImage object
            index: Image index
            process_callback: Optional callback function
            timestamp_folder: Folder to save results

        Returns:
            DetectionResult object
        """
        window_name = captured_image.window_name
        filename = captured_image.filename

        # Convert image to OpenCV format once
        try:
            cv2_image = pil_to_cv2(captured_image.image)
        except Exception as e:
            raise Exception(f"    ❌ Error converting image {window_name}: {str(e)}")

        # Detect cards
        try:
            player_cards = PlayerCardReader(
                self.player_templates,
                PlayerCardReader.DEFAULT_SEARCH_REGION
            ).read(cv2_image)

            table_cards = TableCardReader(self.table_templates, None).read(cv2_image)
        except Exception as e:
            raise Exception(f"    ❌ Error detecting cards in {window_name}: {str(e)}")

        # Detect all player positions
        player_positions = {}
        if self.detect_positions and self.position_templates:
            player_positions = self._check_all_player_positions(cv2_image)
            if player_positions:
                print(f"  👤 Player positions at '{window_name}':")
                for player_num, position in sorted(player_positions.items()):
                    position_type = "Main player" if player_num == 1 else f"Player {player_num}"
                    print(f"     {position_type}: {position}")

        # Check if it's player's move
        is_player_move = self._check_player_move(cv2_image, window_name)

        # Create DetectionResult object
        result = DetectionResult(
            window_name=window_name,
            filename=filename,
            captured_image=captured_image,
            player_cards=player_cards,
            table_cards=table_cards,
            positions=player_positions,  # Now it's the dict mapping player -> position
            is_player_move=is_player_move
        )

        # Print processing info
        print(f"\n📷 Processing image {index + 1}: {window_name}")
        print("-" * 40)

        # Print detection results
        print_detection_result(result)

        # Write result file
        if self.write_detection_files:
            result_filename = f"detection_{filename}.txt"
            write_combined_result(result, timestamp_folder, result_filename, index)

        # Save result image
        if self.save_result_images:
            save_detection_result_image(timestamp_folder, captured_image, result)

        # Call callback if provided
        if process_callback:
            process_callback(index, captured_image, result)

        return result

    def _check_player_move(self, cv2_image, window_name: str) -> bool:
        """
        Check if it's the player's turn to move by detecting move option buttons

        Args:
            cv2_image: OpenCV format image
            window_name: Name of the window for logging

        Returns:
            True if move options are detected, False otherwise
        """
        if not self._player_move_reader:
            return False

        try:
            # Read move options
            detected_moves = self._player_move_reader.read(cv2_image)

            # Log the result
            if detected_moves:
                move_types = [move.move_type for move in detected_moves]
                print(f"🎯 Player's move detected in {window_name}! Options: {', '.join(move_types)}")
                return True
            else:
                print(f"⏸️ Not player's move in {window_name} - no action buttons detected")
                return False

        except Exception as e:
            print(f"❌ Error checking player move in {window_name}: {str(e)}")
            return False

    def detect_stake(self, captured_image, x: int, y: int, w: int, h: int) -> str:
        """
        Detects the bid (stake) in a poker table screenshot.

        Parameters
        ----------
        img_path : str
            Path to the poker-table image file.
        x, y : int
            Top-left corner of the ROI bubble.
        w, h : int
            Width and height of the ROI bubble.

        Returns
        -------
        str
            The OCR’d stake (e.g. "2.50") or an empty string if nothing was found.
        """
        # 1. Load and convert to grayscale
        cv2_image = pil_to_cv2(captured_image.image)

        gray = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2GRAY)

        # 2. Crop to the bubble ROI
        crop = gray[y: y + h, x: x + w]

        # 3. Binarize (invert so text is white on black)
        _, thresh = cv2.threshold(
            crop, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU
        )

        # 4. Upscale to make the dot thicker
        upscaled = cv2.resize(
            thresh, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC
        )

        # 5. Dilate to merge any broken bits of the dot or digits
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        dilated = cv2.dilate(upscaled, kernel, iterations=1)

        # 6. OCR with a strict whitelist and no dictionaries
        config = (
            "--psm 7 --oem 3 "
            "-c tessedit_char_whitelist=0123456789. "
            "-c load_system_dawg=0 -c load_freq_dawg=0"
        )
        text = pytesseract.image_to_string(dilated, config=config).strip()

        return text
