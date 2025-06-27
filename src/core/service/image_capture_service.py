#!/usr/bin/env python3
"""
Image capture service that handles window capture and change detection.
Extracted from DetectionService for better separation of concerns.
"""
from typing import List, Dict

from src.core.domain.captured_image import CapturedWindow
from src.core.utils.capture_utils import capture_and_save_windows


class ImageCaptureService:
    def __init__(self, debug_mode: bool = True):
        self.debug_mode = debug_mode
        self._window_hashes: Dict[str, str] = {}

    def get_changed_images(self, timestamp_folder) -> List[CapturedWindow]:
        captured_windows = self.capture_windows(timestamp_folder)

        if not captured_windows:
            print("🚫 No poker tables detected")
            return []

        changed_images = []
        current_hashes = {}

        for captured_window in captured_windows:
            window_name = captured_window.window_name
            current_hash = captured_window.calculate_hash()
            current_hashes[window_name] = current_hash

            if self._window_hashes.get(window_name) != current_hash:
                changed_images.append(captured_window)

        # Update stored hashes and cleanup removed windows
        self._window_hashes = current_hashes

        if changed_images:
            print(f"🔍 Processing {len(changed_images)} changed/new images out of {len(captured_windows)} total")
        else:
            print("📊 All windows unchanged")

        return changed_images

    def capture_windows(self, timestamp_folder: str) -> List[CapturedWindow]:
        return capture_and_save_windows(
            timestamp_folder=timestamp_folder,
            save_windows=not self.debug_mode,
            debug=self.debug_mode
        )

