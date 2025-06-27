#!/usr/bin/env python3
"""
Detection service that handles card detection and state management.
Refactored to remove threading - detection is triggered by external callers.
"""
import os
from typing import Dict, List
from enum import Enum

from src.core.service.detection_notifier import DetectionNotifier
from src.core.service.game_state_manager import GameStateManager
from src.core.service.image_capture_service import ImageCaptureService
from src.core.utils.fs_utils import create_timestamp_folder
from src.core.utils.poker_game_processor import PokerGameProcessor
from src.core.domain.game import Game
from src.core.domain.captured_image import CapturedImage


class ImageAcquisitionStrategy(Enum):
    """Strategy for acquiring images to process"""
    CHANGED_ONLY = "changed_only"  # Only process changed images
    FORCE_ALL = "force_all"  # Process all images regardless of changes


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
            move_templates_dir=os.path.join(project_root, "resources", "templates", "turn_options"),
            detect_positions=True,
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
        Standard detection cycle with change detection and conditional notification.
        Only processes changed images and only notifies if changes detected.

        Returns:
            List of Game instances with current detections
        """
        return self._execute_detection_cycle(
            strategy=ImageAcquisitionStrategy.CHANGED_ONLY,
            always_notify=False
        )

    def force_detect(self) -> List[Game]:
        """
        Force detection regardless of image changes (for testing/debugging).
        Processes all images and always notifies observers.

        Returns:
            List of Game instances with current detections
        """
        return self._execute_detection_cycle(
            strategy=ImageAcquisitionStrategy.FORCE_ALL,
            always_notify=True
        )

    def _execute_detection_cycle(self,
                                 strategy: ImageAcquisitionStrategy,
                                 always_notify: bool) -> List[Game]:
        """
        Core detection logic shared between detect_and_notify and force_detect.

        Args:
            strategy: Image acquisition strategy (changed only vs all images)
            always_notify: If True, notify observers even if no changes detected

        Returns:
            List of Game instances with current detections
        """
        try:
            # Step 1: Create timestamp folder
            timestamp_folder = create_timestamp_folder(self.debug_mode)

            # Step 2: Get images to process based on strategy
            images_to_process = self._get_images_by_strategy(strategy, timestamp_folder)

            if not images_to_process:
                print("🚫 No poker tables detected or no changes")
                return self._get_current_games()

            # Step 3: Process images
            processed_results = self._poker_game_processor.process_images(
                captured_images=images_to_process,
                timestamp_folder=timestamp_folder,
            )

            # Step 4: Update state and determine if notification needed
            should_notify = self._update_state_and_check_notification(
                processed_results,
                timestamp_folder,
                strategy,
                always_notify
            )

            # Step 5: Notify observers if needed
            if should_notify:
                self._notify_observers(strategy)

            # Step 6: Return current games
            return self._get_current_games()

        except Exception as e:
            print(f"❌ Error in detection: {str(e)}")
            return []

    def _get_images_by_strategy(self,
                                strategy: ImageAcquisitionStrategy,
                                timestamp_folder: str) -> List[CapturedImage]:
        """
        Get images to process based on the acquisition strategy.

        Args:
            strategy: Image acquisition strategy
            timestamp_folder: Timestamp folder for saving/loading images

        Returns:
            List of CapturedImage objects to process
        """
        if strategy == ImageAcquisitionStrategy.CHANGED_ONLY:
            # Standard mode: only process changed images
            return self.image_capture_service.get_images_to_process(timestamp_folder)

        elif strategy == ImageAcquisitionStrategy.FORCE_ALL:
            # Force mode: process all images regardless of changes
            captured_windows = self.image_capture_service.capture_windows(timestamp_folder)

            if captured_windows:
                print(f"🔍 Force processing {len(captured_windows)} images")

            return captured_windows

        else:
            raise ValueError(f"Unknown image acquisition strategy: {strategy}")

    def _update_state_and_check_notification(self,
                                             processed_results,
                                             timestamp_folder: str,
                                             strategy: ImageAcquisitionStrategy,
                                             always_notify: bool) -> bool:
        """
        Update game state and determine if observers should be notified.

        Args:
            processed_results: Results from processing images
            timestamp_folder: Timestamp folder path
            strategy: Image acquisition strategy used
            always_notify: If True, always return True regardless of changes

        Returns:
            True if observers should be notified, False otherwise
        """
        if strategy == ImageAcquisitionStrategy.FORCE_ALL:
            # Force mode: always update state (ignore change detection)
            self.game_state_manager.update_state(processed_results, timestamp_folder)
            return always_notify
        else:
            # Standard mode: only notify if changes detected
            has_changed = self.game_state_manager.update_state(processed_results, timestamp_folder)
            return has_changed or always_notify

    def _notify_observers(self, strategy: ImageAcquisitionStrategy):
        """
        Notify observers with appropriate messaging based on strategy.

        Args:
            strategy: Image acquisition strategy used
        """
        notification_data = self.game_state_manager.get_notification_data()
        self.notifier.notify_observers(notification_data)

        if strategy == ImageAcquisitionStrategy.FORCE_ALL:
            print(f"🔄 Force detection completed - notified observers")
        else:
            print(f"🔄 Detection changed - notified observers at {notification_data['last_update']}")

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