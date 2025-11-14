import os
import traceback
import uuid
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

from table_detector.services.image_capture_service import ImageCaptureService
from table_detector.services.poker_game_processor import PokerGameProcessor
from table_detector.utils.fs_utils import create_timestamp_folder, create_window_folder
from table_detector.utils.log_accumulator import LogAccumulator
from table_detector.utils.windows_utils import initialize_platform
from shared.protocol.message_protocol import GameUpdateMessage, TableRemovalMessage


class DetectionClient:
    def __init__(self, client_id: str = None, detection_interval: int = 10, server_connector=None):
        initialize_platform()

        self.client_id = client_id or f"client_{uuid.uuid4().hex[:8]}"
        self.detection_interval = detection_interval
        self.http_connector = server_connector  # SimpleHttpConnector

        # Initialize detection services (reuse existing components)
        self.image_capture_service = ImageCaptureService()
        self.poker_game_processor = PokerGameProcessor()
        self.debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        self.scheduler = BackgroundScheduler()
        self._setup_scheduler()

        logger.info(f"🎯 Detection client initialized: {self.client_id}")

    def _setup_scheduler(self):
        self.scheduler.add_job(
            func=self.detect_and_send,
            trigger='interval',
            seconds=self.detection_interval,
            id='detect_and_send',
            coalesce=True,
            name='Poker Detection and Send Job',
            replace_existing=True,
            max_instances=1,
        )

    def start_detection(self):
        """Start the detection scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info(f"✅ Detection started (interval: {self.detection_interval}s)")
        else:
            logger.info("⚠️ Detection is already running")

    def stop_detection(self):
        """Stop the detection scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("✅ Detection stopped")
        else:
            logger.info("⚠️ Detection is not running")

    def is_detection_running(self) -> bool:
        return self.scheduler.running

    def detect_and_send(self):
        """Main detection loop - detect game state and send to server."""
        log_accumulator = LogAccumulator() if not self.debug_mode else None

        try:
            # Start capturing logs to memory (if not in debug mode)
            if log_accumulator:
                log_accumulator.start_capture()

            base_timestamp_folder = create_timestamp_folder(self.debug_mode)
            window_changes = self.image_capture_service.get_changed_images(base_timestamp_folder)

            # Only process and write logs if there are changed windows
            if window_changes.changed_images:
                # Process changed windows and collect changed game states
                changed_games = self._handle_changed_windows(window_changes.changed_images, base_timestamp_folder)

                # Handle removed windows and collect removal messages
                removal_messages = self._handle_removed_windows(window_changes.removed_windows)

                # Send updates to server (let the method handle empty inputs)
                self._send_updates_to_server(changed_games, removal_messages)

                # Write accumulated logs to file
                if log_accumulator and log_accumulator.has_logs():
                    log_accumulator.write_to_file(base_timestamp_folder / "app.log")
            else:
                # No changes detected - clear accumulated logs
                if log_accumulator:
                    log_accumulator.clear()

        except Exception as e:
            logger.error(f"Error in detection cycle: {str(e)}")
            traceback.print_exc()

            # Write logs on error too (for debugging)
            if log_accumulator and log_accumulator.has_logs():
                base_timestamp_folder = create_timestamp_folder(self.debug_mode)
                log_accumulator.write_to_file(base_timestamp_folder / "app.log")

        finally:
            # Always cleanup the log handler
            if log_accumulator:
                log_accumulator.stop_capture()

    def _handle_changed_windows(self, captured_windows, base_timestamp_folder):
        """Process changed windows using existing poker game processor and return list of changed game states."""
        changed_games = []

        for i, captured_image in enumerate(captured_windows):
            try:
                logger.info(f"\n📷 Processing image {i + 1}: {captured_image.window_name}")
                logger.info("-" * 40)

                # Create window-specific folder
                window_folder = create_window_folder(base_timestamp_folder, captured_image.window_name)

                # Process and get GameSnapshot
                game_snapshot = self.poker_game_processor.process_window(captured_image, window_folder)

                if game_snapshot:
                    # Store tuple of (game_snapshot, window_name) for later processing
                    changed_games.append((game_snapshot, captured_image.window_name))
                    logger.debug(f"✅ Captured changes for {captured_image.window_name}")
            except Exception as e:
                logger.error(f"Error in detection cycle: {str(e)}\n{traceback.format_exc()}")
                logger.error(f"❌ Error processing {captured_image.window_name}: {str(e)}")
            finally:
                # Clean up the image immediately after processing to prevent memory leaks
                captured_image.close()

        return changed_games

    def _handle_removed_windows(self, removed_window_names):
        """Handle removed windows and return removal message data for transmission."""
        logger.info(f"🗑️ Removing {len(removed_window_names)} closed windows")

        removal_messages = []
        for window_name in removed_window_names:
            logger.info(f"    Removing: {window_name}")

            # Create removal message data structure
            removal_data = {
                'type': 'table_removal',
                'client_id': self.client_id,
                'window_name': window_name,
                'timestamp': datetime.now().isoformat()
            }
            removal_messages.append(removal_data)

        return removal_messages

    def _send_updates_to_server(self, changed_games=None, removal_messages=None):
        """Send specific changed game states and removal messages to servers via HTTP requests.

        Args:
            changed_games: List of (game_snapshot, window_name) tuples to send.
            removal_messages: List of removal message dicts to send.
        """
        if not self.http_connector:
            logger.debug("No HTTP connector configured - skipping server updates")
            return

        try:
            # Send changed games (if any)
            if changed_games:
                logger.debug(f"Sending {len(changed_games)} changed game states to server")
                for game_snapshot, window_name in changed_games:
                    self._send_game_update(game_snapshot, window_name)

            # Send removal messages (if any)
            if removal_messages:
                logger.debug(f"Sending {len(removal_messages)} removal messages to server")
                for removal_data in removal_messages:
                    self._send_removal_update(removal_data)

            # Log if nothing to send
            if not changed_games and not removal_messages:
                logger.debug("No game data or removal messages to send to server")

        except Exception as e:
            logger.debug(f"Error sending updates to server: {str(e)}")
            # Continue detection regardless of server errors

    def _send_game_update(self, game_snapshot, window_name: str):
        """Send individual game update via HTTP."""
        try:
            # Convert GameSnapshot directly to GameUpdateMessage
            game_update = game_snapshot.to_game_update_message(
                client_id=self.client_id,
                window_name=window_name,
                detection_interval=self.detection_interval
            )

            # Simple HTTP request - fire and forget
            self.http_connector.send_game_update(game_update)

        except Exception as e:
            logger.debug(f"Failed to send game update for {window_name}: {str(e)}")

    def _send_removal_update(self, removal_data: dict):
        """Send individual removal message via HTTP."""
        try:
            # Convert removal data to message protocol
            removal_message = TableRemovalMessage(
                type=removal_data.get('type', 'table_removal'),
                client_id=removal_data.get('client_id'),
                removed_windows=[removal_data.get('window_name')],  # Convert single window to list
                timestamp=removal_data.get('timestamp')
            )

            # Simple HTTP request - fire and forget
            self.http_connector.send_removal_message(removal_message)

        except Exception as e:
            logger.debug(f"Failed to send removal update for {removal_data.get('window_name', 'unknown')}: {str(e)}")

    def get_client_id(self) -> str:
        """Get the client ID."""
        return self.client_id
