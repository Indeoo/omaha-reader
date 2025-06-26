#!/usr/bin/env python3
"""
Detection service that handles card detection and state management.
Separated from web service for better code organization.
"""
import os
import threading
import time
from datetime import datetime
from typing import List, Callable, Optional

from src.utils.capture_utils import capture_and_save_windows
from src.utils.shared_processing import PokerGameProcessor, format_results_to_games


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

    def _has_detection_changed(self, new_games, old_games) -> bool:
        """Check if detection results have actually changed"""
        if len(new_games) != len(old_games):
            return True

        for new_game, old_game in zip(new_games, old_games):
            if (new_game.player_cards_string != old_game.player_cards_string or
                    new_game.table_cards_string != old_game.table_cards_string):
                return True

        return False

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
                captured_images = capture_and_save_windows(
                    timestamp_folder=timestamp_folder,
                    save_windows=not self.debug_mode,
                    debug=self.debug_mode
                )

                if len(captured_images) > 1:
                    # Process all captured images using shared function
                    processed_results = self._poker_game_processor.process_images(
                        captured_images=captured_images,
                        timestamp_folder=timestamp_folder,
                    )

                    games = format_results_to_games(processed_results)

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
                        print(f"📊 No changes detected - skipping notification")
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