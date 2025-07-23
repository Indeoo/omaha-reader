import os

from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

from src.core.service.detection_notifier import DetectionNotifier
from src.core.service.game_state_service import GameStateService
from src.core.service.image_capture_service import ImageCaptureService
from src.core.service.state_repository import GameStateRepository
from src.core.utils.fs_utils import create_timestamp_folder, create_window_folder
from src.core.utils.logs import load_logger
from src.core.service.poker_game_processor import PokerGameProcessor
from src.core.utils.windows_utils import initialize_platform


class OmahaEngine:
    def __init__(self, country="canada", debug_mode: bool = True, detection_interval: int = 10):
        initialize_platform()

        self.debug_mode = debug_mode
        self.detection_interval = detection_interval

        self.image_capture_service = ImageCaptureService(debug_mode=debug_mode)
        self.notifier = DetectionNotifier()
        self.game_state_repository = GameStateRepository()
        self.game_state_service = GameStateService(self.game_state_repository)

        self.poker_game_processor = PokerGameProcessor(
            self.game_state_service,
            country=country,
            save_result_images=False,
            write_detection_files=False
        )

        self.scheduler = BackgroundScheduler()
        self._setup_scheduler()

    def _setup_scheduler(self):
        self.scheduler.add_job(
            func=self.detect_and_notify,
            trigger='interval',
            seconds=self.detection_interval,
            id='detect_and_notify',
            name='Poker Detection Job',
            replace_existing=True
        )

    def add_observer(self, callback):
        self.notifier.add_observer(callback)

    def start_scheduler(self):
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info(f"✅ Detection scheduler started (interval: {self.detection_interval}s)")
        else:
            logger.info("⚠️ Detection scheduler is already running")

    def stop_scheduler(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("✅ Detection scheduler stopped")
        else:
            logger.info("⚠️ Detection scheduler is not running")

    def is_scheduler_running(self) -> bool:
        return self.scheduler.running

    def detect_and_notify(self):
        base_timestamp_folder = create_timestamp_folder(self.debug_mode)
        load_logger(base_timestamp_folder)
        window_changes = self.image_capture_service.get_changed_images(base_timestamp_folder)

        changes_detected = False

        if window_changes.changed_images:
            self._handle_changed_windows(window_changes.changed_images, base_timestamp_folder)
            changes_detected = True

        if window_changes.removed_windows:
            self._handle_removed_windows(window_changes.removed_windows)
            changes_detected = True

        if changes_detected:
            self._notify_observers()

    def _handle_changed_windows(self, captured_windows, base_timestamp_folder):
        for i, captured_image in enumerate(captured_windows):
            try:
                logger.info(f"\n📷 Processing image {i + 1}: {captured_image.window_name}")
                logger.info("-" * 40)

                # Create window-specific folder
                window_folder = create_window_folder(base_timestamp_folder, captured_image.window_name)

                self.poker_game_processor.process(captured_image, window_folder)

            except Exception as e:
                logger.error(f"❌ Error processing {captured_image.window_name}: {str(e)}")

    def _handle_removed_windows(self, removed_window_names):
        logger.info(f"🗑️ Removing {len(removed_window_names)} closed windows from state")
        for window_name in removed_window_names:
            logger.info(f"    Removing: {window_name}")

        self.game_state_service.remove_windows(removed_window_names)

    def _notify_observers(self):
        notification_data = self.game_state_service.get_notification_data()
        self.notifier.notify_observers(notification_data)
        logger.info(f"🔄 Detection changed - notified observers at {notification_data['last_update']}")