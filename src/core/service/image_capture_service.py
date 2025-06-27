#!/usr/bin/env python3
"""
Image capture service that handles window capture and change detection.
Extracted from DetectionService for better separation of concerns.
"""
import threading
from typing import List, Dict

from src.core.domain.captured_image import CapturedWindow
from src.core.utils.capture_utils import capture_and_save_windows


class ImageCaptureService:
    """
    Service responsible for capturing windows and detecting image changes.
    Tracks image hashes to determine which windows have changed.
    """

    def __init__(self, debug_mode: bool = True):
        self.debug_mode = debug_mode

        # Window hash tracking - maps window_name to image hash
        self._window_hashes: Dict[str, str] = {}
        self._hash_lock = threading.Lock()

    def get_images_to_process(self, timestamp_folder) -> List[CapturedWindow]:
        """Get images that need processing (changed or new windows)"""
        captured_windows = self._capture_windows(timestamp_folder)

        if not captured_windows:
            print("🚫 No poker tables detected")
            return []

        # Filter to only changed images
        changed_images = self._get_changed_images(captured_windows)
        print(f"🔍 Processing {len(changed_images)} changed/new images out of {len(captured_windows)} total")

        return changed_images

    def _capture_windows(self, timestamp_folder: str) -> List[CapturedWindow]:
        """
        Capture poker windows and return CapturedImage objects

        Args:
            timestamp_folder: Folder path for saving images (if not debug mode)

        Returns:
            List of CapturedImage objects
        """
        captured_windows = capture_and_save_windows(
            timestamp_folder=timestamp_folder,
            save_windows=not self.debug_mode,
            debug=self.debug_mode
        )
        return captured_windows

    def _get_changed_images(self, captured_windows: List[CapturedWindow]) -> List[CapturedWindow]:
        """
        Determine which captured images need processing based on hash comparison

        Args:
            captured_windows: List of CapturedImage objects

        Returns:
            List of images that need processing (changed or new)
        """
        images_to_process = []
        current_window_hashes = {}

        with self._hash_lock:
            all_unchanged = True  # Track if all windows are unchanged

            for captured_window in captured_windows:
                window_name = captured_window.window_name

                # Calculate hash for current image
                current_hash = captured_window.calculate_hash()
                current_window_hashes[window_name] = current_hash

                # Check if this window is new or changed
                stored_hash = self._window_hashes.get(window_name)

                if stored_hash is None:
                    # New window
                    print(f"🆕 New window detected: {window_name}")
                    images_to_process.append(captured_window)
                    all_unchanged = False
                elif stored_hash != current_hash:
                    # Changed window
                    print(f"🔄 Window changed: {window_name}")
                    images_to_process.append(captured_window)
                    all_unchanged = False
                else:
                    # Unchanged window
                    if not all_unchanged:
                        print(f"📊 Window unchanged: {window_name}")

            if all_unchanged:
                print("📊 All windows were unchanged")

            # Update stored hashes with current ones
            self._window_hashes.update(current_window_hashes)

            # Clean up hashes for windows that no longer exist
            current_window_names = set(current_window_hashes.keys())
            stored_window_names = set(self._window_hashes.keys())
            removed_windows = stored_window_names - current_window_names

            for removed_window in removed_windows:
                del self._window_hashes[removed_window]
                print(f"🗑️ Removed hash for closed window: {removed_window}")

        return images_to_process

    def get_window_hash_stats(self) -> Dict[str, str]:
        """Get current window hash statistics for debugging"""
        with self._hash_lock:
            return self._window_hashes.copy()

