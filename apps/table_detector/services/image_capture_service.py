import os
from typing import List, Dict, NamedTuple

from loguru import logger

from table_detector.domain.captured_window import CapturedWindow
from table_detector.services.window_capture_service import capture_and_save_windows


class WindowChanges(NamedTuple):
    changed_images: List[CapturedWindow]
    removed_windows: List[str]


class ImageCaptureService:
    def __init__(self):
        self.debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        self._window_hashes: Dict[str, str] = {}

    def get_changed_images(self, base_timestamp_folder) -> WindowChanges:
        captured_windows = capture_and_save_windows(
            timestamp_folder=base_timestamp_folder,
            save_windows=not self.debug_mode,
            debug=self.debug_mode
        )

        if not captured_windows:
            logger.warning("🚫 No poker tables detected")
            removed_windows = list(self._window_hashes.keys())
            self._window_hashes.clear()
            return WindowChanges(changed_images=[], removed_windows=removed_windows)

        changed_images = []
        unchanged_windows = []
        current_hashes = {}
        current_window_names = set()

        for captured_window in captured_windows:
            window_name = captured_window.window_name
            current_window_names.add(window_name)
            current_hash = captured_window.calculate_hash()
            current_hashes[window_name] = current_hash

            if self._window_hashes.get(window_name) != current_hash:
                changed_images.append(captured_window)
            else:
                unchanged_windows.append(captured_window)

        # Clean up unchanged images immediately to prevent memory leaks
        for unchanged_window in unchanged_windows:
            unchanged_window.close()

        previous_window_names = set(self._window_hashes.keys())
        removed_windows = list(previous_window_names - current_window_names)

        self._window_hashes = current_hashes

        if changed_images:
            logger.info(f"🔍 Processing {len(changed_images)} changed/new images out of {len(captured_windows)} total")

        if removed_windows:
            logger.info(f"🗑️ Detected {len(removed_windows)} removed windows: {removed_windows}")

        if not changed_images and not removed_windows:
            logger.info("📊 All windows unchanged")

        return WindowChanges(changed_images=changed_images, removed_windows=removed_windows)
