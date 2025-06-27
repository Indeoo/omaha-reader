#!/usr/bin/env python3
"""
Detection service that handles card detection and state management.
Refactored to remove threading - detection is triggered by external callers.
"""
import os
from typing import Dict, List

from src.core.service.detection_notifier import DetectionNotifier
from src.core.service.game_state_manager import GameStateManager
from src.core.service.image_capture_service import ImageCaptureService
from src.core.utils.poker_game_processor import PokerGameProcessor
from src.core.domain.game import Game


class OmahaGameReader:
    """
    Service responsible for detecting cards and managing state.
    Pure detection + observer pattern, no threading.
    External callers control timing by calling detect_and_notify().
    """

    def __init__(self, debug_mode: bool = True):
        self.debug_mode = debug_mode

        # Initialize services
        self.image_capture_service = ImageCaptureService(debug_mode=debug_mode)
        self.notifier = DetectionNotifier()
        self.game_state_manager = GameStateManager()

        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))

        # Build absolute paths
        self._poker_game_processor = PokerGameProcessor(
            player_templates_dir=os.path.join(project_root, "resources", "templates", "player_cards"),
            table_templates_dir=os.path.join(project_root, "resources", "templates", "table_cards"),
            position_templates_dir=os.path.join(project_root, "resources", "templates", "positions"),
            detect_positions=False,
            save_result_images=False,
            write_detection_files=False
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

    def detect_and_notify(self) -> List[Game]:
        """
        Simplified detection cycle with observer notification.
        External callers control timing by calling this method.

        Returns:
            List of Game instances with current detections
        """
        try:
            # Get timestamp folder and capture changed images
            timestamp_folder = self.image_capture_service.create_timestamp_folder()
            images_to_process = self.image_capture_service.get_images_to_process(timestamp_folder)

            if not images_to_process:
                print("🚫 No poker tables detected or no changes")
                return self._get_current_games()

            # Process changed images
            processed_results = self._poker_game_processor.process_images(
                captured_images=images_to_process,
                timestamp_folder=timestamp_folder,
            )

            # Update state and notify if changed
            has_changed = self.game_state_manager.update_state(processed_results, timestamp_folder)

            if has_changed:
                notification_data = self.game_state_manager.get_notification_data()
                self.notifier.notify_observers(notification_data)
                print(f"🔄 Detection changed - notified observers at {notification_data['last_update']}")
            else:
                print(f"📊 Detection results unchanged - skipping notification")

            return self._get_current_games()

        except Exception as e:
            print(f"❌ Error in detection: {str(e)}")
            return []

    def force_detect(self) -> List[Game]:
        """
        Force detection regardless of image changes (for testing/debugging).

        Returns:
            List of Game instances with current detections
        """
        try:
            # Create timestamp folder
            timestamp_folder = self.image_capture_service.create_timestamp_folder()

            # Capture windows
            captured_windows = self.image_capture_service.capture_windows(timestamp_folder)

            if captured_windows:
                print(f"🔍 Force processing {len(captured_windows)} images")

                # Process all images (ignore hash comparison)
                processed_results = self._poker_game_processor.process_images(
                    captured_images=captured_windows,
                    timestamp_folder=timestamp_folder,
                )

                # Force update state (ignore change detection)
                self.game_state_manager.update_state(processed_results, timestamp_folder)

                # Always notify observers on force detect
                notification_data = self.game_state_manager.get_notification_data()
                self.notifier.notify_observers(notification_data)

                print(f"🔄 Force detection completed - notified observers")
                return self._get_current_games()
            else:
                print("🚫 No poker tables detected")
                return []

        except Exception as e:
            print(f"❌ Error in force detection: {str(e)}")
            return []

    def _get_current_games(self) -> List[Game]:
        """Get current games as Game instances (not dictionaries)"""
        latest_results = self.game_state_manager.get_latest_results()

        # Convert dictionaries back to Game instances
        games = []
        for game_dict in latest_results.get('detections', []):
            # Create Game from dictionary (assuming Game.from_dict exists or manual creation)
            game = Game(
                window_name=game_dict['window_name'],
                player_cards=[],  # These would need reconstruction from dict
                table_cards=[]  # These would need reconstruction from dict
            )
            games.append(game)

        return games

    def get_window_hash_stats(self) -> Dict[str, str]:
        """Get current window hash statistics for debugging"""
        return self.image_capture_service.get_window_hash_stats()

    def clear_state(self):
        """Clear all stored state (useful for testing or reset)"""
        self.game_state_manager.clear_state()
        self.image_capture_service.clear_window_hashes()
