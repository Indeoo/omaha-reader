import threading
import time

from src.core.omaha_engine import OmahaEngine


class DetectionScheduler:
    """Handles scheduling of detection cycles"""

    def __init__(self, detection_service: OmahaEngine, wait_time: int):
        self.detection_service = detection_service
        self.wait_time = wait_time
        self._running = False
        self._scheduler_thread = None

    def start(self):
        """Start the detection scheduler"""
        if self._running:
            print("⚠️ Detection scheduler is already running")
            return

        self._running = True
        self._scheduler_thread = threading.Thread(target=self._scheduler_worker, daemon=True)
        self._scheduler_thread.start()
        print(f"✅ Detection scheduler started (interval: {self.wait_time}s)")

    def stop(self):
        """Stop the detection scheduler"""
        if not self._running:
            print("⚠️ Detection scheduler is not running")
            return

        self._running = False
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._scheduler_thread.join(timeout=5)
        print("✅ Detection scheduler stopped")

    def _scheduler_worker(self):
        """Background worker that triggers detection at intervals"""
        print("🎯 Detection scheduler worker started")

        while self._running:
            try:
                # Trigger detection
                self.detection_service.detect_and_notify()
            except Exception as e:
                print(f"❌ Error in scheduled detection: {str(e)}")

            # Wait before next detection
            if self._running:  # Check if still running before sleeping
                time.sleep(self.wait_time)

        print("🛑 Detection scheduler worker stopped")

    def is_running(self) -> bool:
        """Check if the scheduler is running"""
        return self._running