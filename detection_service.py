#!/usr/bin/env python3
"""
Detection service that handles card detection and state management.
Separated from web service for better code organization.
"""
import os
import threading
import time
from datetime import datetime
from typing import List, Callable, Dict

from src.domain.detection_result import DetectionResult
from src.domain.game import Game
from src.domain.captured_image import CapturedImage
from src.utils.capture_utils import capture_and_save_windows
from src.utils.poker_game_processor import PokerGameProcessor


class DetectionService:
    """
    Service responsible for capturing windows, detecting cards, and managing state.
    Runs in a background thread and notifies observers when detection results change.
    """

    def __init__(self, wait_time: int = 5, debug_mode: bool = True):
        self.wait_time = wait_time
        self.debug_mode = debug_mode

        # State management
        self._latest_results = {
            'timestamp': None,
            'detections': [],  # List of Game instances
            'last_update': None
        }
        self._state_lock = threading.Lock()

        # Window hash tracking - maps window_name to image hash
        self._window_hashes: Dict[str, str] = {}
        self._hash_lock = threading.Lock()

        # Thread management
        self._worker_thread = None
        self._running = False

        # Observer pattern for notifications
        self._observers: List[Callable] = []

        # Initialize poker game processor
        self._poker_game_processor = PokerGameProcessor(
            player_templates_dir="resources/templates/player_cards/",
            table_templates_dir="resources/templates/table_cards/",
            position_templates_dir="resources/templates/positions/",
            detect_positions=False,  # Web version doesn't need positions
            save_result_images=False,  # Don't save result images in web mode
            write_detection_files=False  # Don't write files in web mode
        )

        self._previous_games = []

    def add_observer(self, callback: Callable[[dict], None]):
        """Add an observer that will be notified when detection results change"""
        self._observers.append(callback)

    def remove_observer(self, callback: Callable[[dict], None]):
        """Remove an observer"""
        if callback in self._observers:
            self._observers.remove(callback)

    def _notify_observers(self, data: dict):
        """Notify all observers of detection changes"""
        for observer in self._observers:
            try:
                observer(data)
            except Exception as e:
                print(f"❌ Error notifying observer: {str(e)}")

    def get_latest_results(self) -> dict:
        """Get the latest detection results (thread-safe)"""
        with self._state_lock:
            # Convert Game instances to dictionaries for JSON serialization
            return {
                'timestamp': self._latest_results['timestamp'],
                'detections': [game.to_dict() for game in self._latest_results['detections']],
                'last_update': self._latest_results['last_update']
            }

    def _get_images_to_process(self, captured_images: List[CapturedImage]) -> List[CapturedImage]:
        """
        Determine which captured images need processing based on hash comparison

        Args:
            captured_images: List of CapturedImage objects

        Returns:
            List of images that need processing (changed or new)
        """
        images_to_process = []
        current_window_hashes = {}

        with self._hash_lock:
            all_unchanged = True  # Track if all windows are unchanged
            for captured_image in captured_images:
                window_name = captured_image.window_name

                # Calculate hash for current image
                current_hash = captured_image.calculate_hash()
                current_window_hashes[window_name] = current_hash

                # Check if this window is new or changed
                stored_hash = self._window_hashes.get(window_name)

                if stored_hash is None:
                    # New window
                    print(f"🆕 New window detected: {window_name}")
                    images_to_process.append(captured_image)
                    all_unchanged = False
                elif stored_hash != current_hash:
                    # Changed window
                    print(f"🔄 Window changed: {window_name}")
                    images_to_process.append(captured_image)
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

    def _has_detection_changed(self, new_games: List[Game], old_games: List[Game]) -> bool:
        """Check if detection results have actually changed"""
        if len(new_games) != len(old_games):
            return True

        for new_game, old_game in zip(new_games, old_games):
            if (new_game.get_player_cards_string() != old_game.get_player_cards_string() or
                    new_game.get_table_cards_string() != old_game.get_table_cards_string()):
                return True

        return False

    def _convert_results_to_games(self, processed_results: List[DetectionResult]) -> List[Game]:
        """
        Convert DetectionResult objects to Game instances

        Args:
            processed_results: List of DetectionResult objects

        Returns:
            List of Game instances
        """
        games = []

        for result in processed_results:
            if result.has_cards:
                # Create game with raw ReadedCard objects
                game = Game(
                    window_name=result.window_name,
                    player_cards=result.player_cards,
                    table_cards=result.table_cards
                )
                games.append(game)

        return games

    def _detection_worker(self):
        """Background worker that continuously captures and detects cards"""
        print("🎯 Detection worker started")

        while self._running:
            try:
                session_timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")

                if self.debug_mode:
                    # Debug mode - use existing folder
                    timestamp_folder = os.path.join(os.getcwd(),
                                                    "Dropbox/data_screenshots/_20250610_023049/_20250610_025342")
                else:
                    # Live mode - create new folder
                    timestamp_folder = os.path.join(os.getcwd(), f"Dropbox/data_screenshots/{session_timestamp}")

                # Capture windows
                captured_windows = capture_and_save_windows(
                    timestamp_folder=timestamp_folder,
                    save_windows=not self.debug_mode,
                    debug=self.debug_mode
                )

                if captured_windows:
                    # Determine which images need processing based on hash comparison
                    images_to_process = self._get_images_to_process(captured_windows)

                    if images_to_process:
                        print(
                            f"🔍 Processing {len(images_to_process)} changed/new images out of {len(captured_windows)} total")

                        # Process only the changed/new images
                        processed_results = self._poker_game_processor.process_images(
                            captured_images=images_to_process,
                            timestamp_folder=timestamp_folder,
                        )

                        games = self._convert_results_to_games(processed_results)

                        # Check if results have changed
                        if self._has_detection_changed(games, self._previous_games):
                            # Update state with Game instances
                            with self._state_lock:
                                self._latest_results = {
                                    'timestamp': session_timestamp,
                                    'detections': games,  # Store Game instances
                                    'last_update': datetime.now().isoformat()
                                }

                            # Notify observers
                            notification_data = {
                                'type': 'detection_update',
                                'timestamp': session_timestamp,
                                'detections': [game.to_dict() for game in games],
                                'last_update': self._latest_results['last_update']
                            }
                            self._notify_observers(notification_data)

                            print(f"🔄 Detection changed - notified observers at {self._latest_results['last_update']}")
                            self._previous_games = games
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
        with self._hash_lock:
            return self._window_hashes.copy()