import traceback
import uuid
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

# Ensure proper path setup
import sys
import os

# Add the current directory to path so we can import local modules
current_dir = os.path.dirname(os.path.abspath(__file__))
apps_dir = os.path.dirname(current_dir)
if apps_dir not in sys.path:
    sys.path.insert(0, apps_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from services.image_capture_service import ImageCaptureService
from services.game_state_service import GameStateService
from services.state_repository import GameStateRepository
from services.poker_game_processor import PokerGameProcessor
from utils.fs_utils import create_timestamp_folder, create_window_folder
from utils.logs import load_logger
from utils.windows_utils import initialize_platform
from shared.protocol.message_protocol import GameUpdateMessage, TableRemovalMessage


class DetectionClient:
    def __init__(self, client_id: str = None, country="canada", debug_mode: bool = True, 
                 detection_interval: int = 10, server_connector=None):
        initialize_platform()

        self.client_id = client_id or f"client_{uuid.uuid4().hex[:8]}"
        self.debug_mode = debug_mode
        self.detection_interval = detection_interval
        self.server_connector = server_connector  # Can be single connector or ServerConnectorManager

        # Initialize detection services (reuse existing components)
        self.image_capture_service = ImageCaptureService(debug_mode=debug_mode)
        self.game_state_repository = GameStateRepository()
        self.game_state_service = GameStateService(self.game_state_repository)

        self.poker_game_processor = PokerGameProcessor(
            self.game_state_service,
            country=country,
            save_result_images=debug_mode,  # Save result images only in debug mode
            write_detection_files=debug_mode  # Write detection files only in debug mode
        )

        self.scheduler = BackgroundScheduler()
        self._setup_scheduler()

        logger.info(f"🎯 Detection client initialized: {self.client_id}")

    def _validate_server_connector(self, operation: str) -> bool:
        """Validate server connector is available."""
        if not self.server_connector:
            logger.error(f"No server connector configured for {operation}")
            return False
        return True

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
        try:
            base_timestamp_folder = create_timestamp_folder(self.debug_mode)
            if not self.debug_mode:
                load_logger(base_timestamp_folder)
            
            window_changes = self.image_capture_service.get_changed_images(base_timestamp_folder)

            changes_detected = False

            # Process changed windows
            if window_changes.changed_images:
                self._handle_changed_windows(window_changes.changed_images, base_timestamp_folder)
                changes_detected = True

            # Handle removed windows
            if window_changes.removed_windows:
                self._handle_removed_windows(window_changes.removed_windows)
                changes_detected = True

            # Send updates to server if changes detected
            if changes_detected:
                self._send_updates_to_server()

        except Exception as e:
            logger.error(f"Error in detection cycle: {str(e)}")
            traceback.print_exc()

    def _handle_changed_windows(self, captured_windows, base_timestamp_folder):
        """Process changed windows using existing poker game processor."""
        for i, captured_image in enumerate(captured_windows):
            try:
                logger.info(f"\n📷 Processing image {i + 1}: {captured_image.window_name}")
                logger.info("-" * 40)

                # Create window-specific folder
                window_folder = create_window_folder(base_timestamp_folder, captured_image.window_name)

                self.poker_game_processor.process(captured_image, window_folder)

            except Exception as e:
                traceback.print_exc()
                logger.error(f"❌ Error processing {captured_image.window_name}: {str(e)}")
            finally:
                # Clean up the image immediately after processing to prevent memory leaks
                captured_image.close()

    def _handle_removed_windows(self, removed_window_names):
        """Handle removed windows."""
        logger.info(f"🗑️ Removing {len(removed_window_names)} closed windows from state")
        for window_name in removed_window_names:
            logger.info(f"    Removing: {window_name}")

        # Send removal message to server before updating local state
        self._send_removal_message(removed_window_names)
        
        # Remove from local state
        self.game_state_service.remove_windows(removed_window_names)

    def _send_updates_to_server(self):
        """Send current game states to server."""
        if not self._validate_server_connector("sending updates"):
            return

        try:
            # Get all current game states
            all_games = self.game_state_service.get_all_games()
            
            if not all_games['detections']:
                logger.info("No game data to send to server")
                return

            # Send each game state as separate message
            for game_data in all_games['detections']:
                self._send_game_update(game_data)

        except Exception as e:
            logger.error(f"Error sending updates to server: {str(e)}")
            traceback.print_exc()

    def _send_game_update(self, game_data: dict):
        """Send individual game update to server."""
        try:
            # Extract game state from existing format and convert to message protocol
            game_update = GameUpdateMessage(
                type='game_update',
                client_id=self.client_id,
                window_name=game_data.get('window_name', 'unknown'),
                timestamp=datetime.now().isoformat(),
                game_data={
                    'player_cards': self._convert_cards_to_protocol(game_data.get('player_cards', [])),
                    'table_cards': self._convert_cards_to_protocol(game_data.get('table_cards', [])),
                    'positions': self._convert_positions_to_protocol(game_data.get('positions', [])),
                    'moves': game_data.get('moves', []),
                    'street': game_data.get('street', 'unknown'),
                    'solver_link': game_data.get('solver_link')
                }
            )

            # Send to server(s) via connector
            if hasattr(self.server_connector, 'send_to_all_servers'):
                # Multi-server setup
                results = self.server_connector.send_to_all_servers(game_update)
                successful_sends = sum(results.values())
                total_servers = len(results)
                
                if successful_sends > 0:
                    logger.info(f"✅ Sent game update to {successful_sends}/{total_servers} servers: {game_data.get('window_name')}")
                else:
                    logger.error(f"❌ Failed to send game update to any server: {game_data.get('window_name')}")
            else:
                # Single server setup (backward compatibility)
                success = self.server_connector.send_game_update(game_update)
                
                if success:
                    logger.info(f"✅ Sent game update to server: {game_data.get('window_name')}")
                else:
                    logger.error(f"❌ Failed to send game update: {game_data.get('window_name')}")

        except Exception as e:
            logger.error(f"Error preparing game update: {str(e)}")

    def _send_removal_message(self, removed_window_names):
        """Send table removal message to server."""
        if not self._validate_server_connector("sending removal message"):
            return

        if not removed_window_names:
            return

        try:
            # Create removal message
            removal_message = TableRemovalMessage(
                type='table_removal',
                client_id=self.client_id,
                removed_windows=removed_window_names,
                timestamp=datetime.now().isoformat()
            )

            # Send to server(s) via connector
            if hasattr(self.server_connector, 'send_to_all_servers'):
                # Multi-server setup
                results = self.server_connector.send_to_all_servers(removal_message)
                successful_sends = sum(results.values())
                total_servers = len(results)
                
                if successful_sends > 0:
                    logger.info(f"✅ Sent removal message to {successful_sends}/{total_servers} servers: {removed_window_names}")
                else:
                    logger.error(f"❌ Failed to send removal message to any server: {removed_window_names}")
            else:
                # Single server setup (backward compatibility)
                success = self.server_connector.send_game_update(removal_message)
                
                if success:
                    logger.info(f"✅ Sent removal message to server: {removed_window_names}")
                else:
                    logger.error(f"❌ Failed to send removal message: {removed_window_names}")

        except Exception as e:
            logger.error(f"Error sending removal message: {str(e)}")

    def _convert_cards_to_protocol(self, cards: list) -> list:
        """Convert card format from web format to protocol format."""
        protocol_cards = []
        for card in cards:
            if isinstance(card, dict):
                protocol_cards.append({
                    'template_name': card.get('name', ''),
                    'match_score': card.get('score', 0),
                    'position': None,  # Not available from web format
                    'name': card.get('name', '')
                })
        return protocol_cards

    def _convert_positions_to_protocol(self, positions: list) -> dict:
        """Convert positions from web format to protocol format."""
        protocol_positions = {}
        for pos in positions:
            if isinstance(pos, dict):
                player_id = pos.get('player', 1)
                protocol_positions[str(player_id)] = {
                    'template_name': pos.get('name', ''),
                    'match_score': 1.0,  # Not available from web format
                    'position': None,  # Not available from web format  
                    'name': pos.get('name', '')
                }
        return protocol_positions

    def register_with_server(self) -> bool:
        """Register this client with all servers."""
        if not self._validate_server_connector("registration"):
            return False

        # Always using ServerConnectorManager now
        results = self.server_connector.register_with_all_servers(self.client_id)
        successful_registrations = sum(results.values())
        return successful_registrations > 0

    def get_client_id(self) -> str:
        """Get the client ID."""
        return self.client_id