#!/usr/bin/env python3
"""
Detection service that handles card detection and state management.
Refactored to use GameStateManager for better separation of concerns.
"""
import threading
import time
from typing import Dict

from src.detection_notifier import DetectionNotifier
from src.game_state_manager import GameStateManager
from src.image_capture_service import ImageCaptureService
from src.utils.poker_game_processor import PokerGameProcessor


class OmahaGameReader:
    """
    Service responsible for detecting cards and managing state.
    Runs in a background thread and notifies observers when detection results change.
    """

    def __init__(self, wait_time: int = 5, debug_mode: bool = True):
        self.wait_time = wait_time
        self.debug_mode = debug_mode

        # Initialize services
        self.image_capture_service = ImageCaptureService(debug_mode=debug_mode)
        self.notifier = DetectionNotifier()
        self.game_state_manager = GameStateManager()

        # Thread management
        self._worker_thread = None
        self._running = False

        # Initialize poker game processor
        self._poker_game_processor = PokerGameProcessor(
            player_templates_dir="resources/templates/player_cards/",
            table_templates_dir="resources/templates/table_cards/",
            position_templates_dir="resources/templates/positions/",
            detect_positions=False,  # Web version doesn't need positions
            save_result_images=False,  # Don't save result images in web mode
            write_detection_files=False  # Don't write files in web mode
        )

    def add_observer(self, callback):
        """Add an observer that will be notified when detection results change"""
        self.notifier.add_observer(callback)

    def remove_observer(self, callback):
        """Remove an observer"""
        self.notifier.remove_observer(callback)

    def get_latest_results(self) -> dict:
        """Get the latest detection results (thread-safe)"""
        return self.game_state_manager.get_latest_results()

    def _detection_worker(self):
        """Background worker that continuously captures and detects cards"""
        print("🎯 Detection worker started")

        while self._running:
            try:
                # Create timestamp folder
                timestamp_folder = self.image_capture_service.create_timestamp_folder()

                # Capture windows
                captured_windows = self.image_capture_service.capture_windows(timestamp_folder)

                if captured_windows:
                    # Determine which images need processing based on hash comparison
                    images_to_process = self.image_capture_service.get_changed_images(captured_windows)

                    if images_to_process:
                        print(
                            f"🔍 Processing {len(images_to_process)} changed/new images out of {len(captured_windows)} total")

                        # Process only the changed/new images
                        processed_results = self._poker_game_processor.process_images(
                            captured_images=images_to_process,
                            timestamp_folder=timestamp_folder,
                        )

                        # Update game state and check if notification is needed
                        has_changed = self.game_state_manager.update_state(processed_results, timestamp_folder)

                        if has_changed:
                            # Notify observers
                            notification_data = self.game_state_manager.get_notification_data()
                            self.notifier.notify_observers(notification_data)

                            print(f"🔄 Detection changed - notified observers at {notification_data['last_update']}")
                        else:
                            print(f"📊 Detection results unchanged - skipping notification")
                    else:
                        print(f"📊 No image changes detected - skipping processing")
                else:
                    print("🚫 No poker tables detected, skipping this cycle")

            except Exception as e:
                print(f"❌ Error in detection worker: {str(e)}")

            # Wait before next capture
            if self._running:  # Check if still running before sleeping
                time.sleep(self.wait_time)

        print("🛑 Detection worker stopped")

    def start(self):
        """Start the detection service"""
        if self._running:
            print("⚠️ Detection service is already running")
            return

        self._running = True
        self._worker_thread = threading.Thread(target=self._detection_worker, daemon=True)
        self._worker_thread.start()
        print("✅ Detection service started")

    def stop(self):
        """Stop the detection service"""
        if not self._running:
            print("⚠️ Detection service is not running")
            return

        self._running = False
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=5)
        print("✅ Detection service stopped")

    def is_running(self) -> bool:
        """Check if the detection service is running"""
        return self._running

    def get_window_hash_stats(self) -> Dict[str, str]:
        """Get current window hash statistics for debugging"""
        return self.image_capture_service.get_window_hash_stats()