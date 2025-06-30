import os
from apscheduler.schedulers.background import BackgroundScheduler

from src.core.service.detection_notifier import DetectionNotifier
from src.core.service.image_capture_service import ImageCaptureService
from src.core.service.state_repository import GameStateRepository
from src.core.utils.fs_utils import create_timestamp_folder
from src.core.utils.poker_game_processor import PokerGameProcessor


class OmahaEngine:
    def __init__(self, country="canada", debug_mode: bool = True, detection_interval: int = 10):
        self.debug_mode = debug_mode
        self.detection_interval = detection_interval

        self.image_capture_service = ImageCaptureService(debug_mode=debug_mode)
        self.notifier = DetectionNotifier()
        self.state_repository = GameStateRepository()

        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))

        self.poker_game_processor = PokerGameProcessor(
            self.state_repository,
            country=country,
            project_root=project_root,
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
            print(f"✅ Detection scheduler started (interval: {self.detection_interval}s)")
        else:
            print("⚠️ Detection scheduler is already running")

    def stop_scheduler(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            print("✅ Detection scheduler stopped")
        else:
            print("⚠️ Detection scheduler is not running")

    def is_scheduler_running(self) -> bool:
        return self.scheduler.running

    def detect_and_notify(self):
        timestamp_folder = create_timestamp_folder(self.debug_mode)
        changed_images = self.image_capture_service.get_changed_images(timestamp_folder)

        if changed_images:
            self._process_windows(changed_images)
            self._notify_observers()

    def _process_windows(self, captured_windows):
        for i, captured_image in enumerate(captured_windows):
            try:
                print(f"\n📷 Processing image {i + 1}: {captured_image.window_name}")
                print("-" * 40)
                self.poker_game_processor.process_window(captured_image)

            except Exception as e:
                print(f"❌ Error processing {captured_image.window_name}: {str(e)}")

    def _notify_observers(self):
        notification_data = self.state_repository.get_notification_data()
        self.notifier.notify_observers(notification_data)
        print(f"🔄 Detection changed - notified observers at {notification_data['last_update']}")