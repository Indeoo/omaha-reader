#!/usr/bin/env python3
"""
Image capture service that handles window capture and change detection.
Extracted from DetectionService for better separation of concerns.
"""
from typing import List, Dict, NamedTuple

from loguru import logger

from src.core.domain.captured_window import CapturedWindow
from src.core.utils.capture_utils import capture_and_save_windows
from src.core.utils.logs import console_logger


class WindowChanges(NamedTuple):
    changed_images: List[CapturedWindow]
    removed_windows: List[str]


class ImageCaptureService:
    def __init__(self, debug_mode: bool = True):
        self.debug_mode = debug_mode
        self._window_hashes: Dict[str, str] = {}

    def get_changed_images(self, timestamp_folder) -> WindowChanges:
        captured_windows = self.capture_windows(timestamp_folder)

        if not captured_windows:
            console_logger.error("🚫 No poker tables detected")
            # All previously tracked windows are now removed
            removed_windows = list(self._window_hashes.keys())
            self._window_hashes.clear()
            return WindowChanges(changed_images=[], removed_windows=removed_windows)

        changed_images = []
        current_hashes = {}
        current_window_names = set()

        for captured_window in captured_windows:
            window_name = captured_window.window_name
            current_window_names.add(window_name)
            current_hash = captured_window.calculate_hash()
            current_hashes[window_name] = current_hash

            if self._window_hashes.get(window_name) != current_hash:
                changed_images.append(captured_window)

        # Find removed windows
        previous_window_names = set(self._window_hashes.keys())
        removed_windows = list(previous_window_names - current_window_names)

        # Update stored hashes
        self._window_hashes = current_hashes

        if changed_images:
            logger.info(f"🔍 Processing {len(changed_images)} changed/new images out of {len(captured_windows)} total")

        if removed_windows:
            logger.info(f"🗑️ Detected {len(removed_windows)} removed windows: {removed_windows}")

        if not changed_images and not removed_windows:
            logger.info("📊 All windows unchanged")

        return WindowChanges(changed_images=changed_images, removed_windows=removed_windows)

    def capture_windows(self, timestamp_folder: str) -> List[CapturedWindow]:
        return capture_and_save_windows(
            timestamp_folder=timestamp_folder,
            save_windows=not self.debug_mode,
            debug=self.debug_mode
        )