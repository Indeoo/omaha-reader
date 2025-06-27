#!/usr/bin/env python3
"""
Shared image processing functions for both main.py and main_web3.py
"""
from typing import Dict, List, Callable

from src.core.domain.captured_image import CapturedImage
from src.core.reader.omaha_card_reader import OmahaCardReader
from src.core.reader.player_position_reader import PlayerPositionReader
from src.core.reader.table_card_reader import TableCardReader
from src.core.utils.benchmark_utils import benchmark
from src.core.utils.detect_utils import save_detection_result_image
from src.core.domain.detection_result import DetectionResult
from src.core.utils.result_utils import print_detection_result, write_combined_result
from src.core.utils.opencv_utils import load_templates, pil_to_cv2


class PokerGameProcessor:
    def __init__(
            self,
            player_templates_dir: str = None,
            table_templates_dir: str = None,
            position_templates_dir: str = None,
            player_templates: Dict = None,
            table_templates: Dict = None,
            position_templates: Dict = None,
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

        self.detect_positions = detect_positions
        self.save_result_images = save_result_images
        self.write_detection_files = write_detection_files

    def process_images(
            self,
            captured_images: List[CapturedImage],
            timestamp_folder: str,
            process_callback: Callable = None,
    ) -> List[DetectionResult]:
        """
        Process a list of captured images to detect cards and optionally positions.

        Args:
            captured_images: List of CapturedImage objects
            timestamp_folder: Folder to save results
            process_callback: Optional callback function called for each processed image
                             with args (i, captured_image, result)

        Returns:
            List of DetectionResult objects containing processed results for each image
        """
        processed_results = []

        for i, captured_image in enumerate(captured_images):
            result = self._process_single_image(captured_image, i, process_callback, timestamp_folder)
            processed_results.append(result)

        return processed_results

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
            player_cards = OmahaCardReader(
                self.player_templates,
                OmahaCardReader.DEFAULT_SEARCH_REGION
            ).read(cv2_image)

            table_cards = TableCardReader(self.table_templates, None).read(cv2_image)
        except Exception as e:
            raise Exception(f"    ❌ Error detecting cards in {window_name}: {str(e)}")

        # Detect positions if enabled
        positions = []
        if self.detect_positions and self.position_templates and window_name:
            try:
                positions = PlayerPositionReader(self.position_templates).read(cv2_image)
            except Exception as e:
                raise Exception(f"    ❌ Error detecting positions in {window_name}: {str(e)}")

        # Create DetectionResult object
        result = DetectionResult(
            window_name=window_name,
            filename=filename,
            captured_image=captured_image,
            player_cards=player_cards,
            table_cards=table_cards,
            positions=positions
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