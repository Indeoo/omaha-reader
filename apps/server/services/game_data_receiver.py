from datetime import datetime
from typing import Optional, Callable

from loguru import logger

from apps.server.services.server_game_state import ServerGameStateService
from apps.shared.protocol.message_protocol import ServerResponseMessage, MessageParser, ClientRegistrationMessage, \
    GameUpdateMessage, TableRemovalMessage


class GameDataReceiver:
    def __init__(self, game_state_service: ServerGameStateService):
        self.game_state_service = game_state_service
        self.global_update_callbacks: list[Callable] = []
        self.client_update_callbacks: list[Callable] = []
        self.client_detection_intervals: dict[str, int] = {}  # Track detection intervals per client

    def add_update_callback(self, callback: Callable[[dict], None]) -> None:
        """Add callback to be called when game state updates occur (legacy - global updates)."""
        self.global_update_callbacks.append(callback)
    
    def add_global_update_callback(self, callback: Callable[[dict], None]) -> None:
        """Add callback for global updates (all clients data)."""
        self.global_update_callbacks.append(callback)
    
    def add_client_update_callback(self, callback: Callable[[str, str, dict], None]) -> None:
        """Add callback for client-specific updates (client_id, window_name, client_data)."""
        self.client_update_callbacks.append(callback)

    def handle_client_message(self, message_json: str, client_id: Optional[str] = None) -> Optional[ServerResponseMessage]:
        """Process incoming message from client and return response if needed."""
        try:
            message = MessageParser.parse_message(message_json)
            
            if message is None:
                logger.error(f"Failed to parse message: {message_json}")
                return MessageParser.create_response("error", "Invalid message format")

            if isinstance(message, ClientRegistrationMessage):
                return self._handle_client_registration(message)
            
            elif isinstance(message, GameUpdateMessage):
                return self._handle_game_update(message)
                
            elif isinstance(message, TableRemovalMessage):
                return self._handle_table_removal(message)
            
            else:
                logger.warning(f"Unknown message type received: {message}")
                return MessageParser.create_response("error", "Unknown message type")

        except Exception as e:
            logger.error(f"Error processing client message: {str(e)}")
            return MessageParser.create_response("error", f"Processing error: {str(e)}")

    def _handle_client_registration(self, message: ClientRegistrationMessage) -> ServerResponseMessage:
        """Handle client registration."""
        try:
            self.game_state_service.register_client(message.client_id)
            # Store the client's detection interval
            self.client_detection_intervals[message.client_id] = message.detection_interval
            logger.info(f"✅ Client registered: {message.client_id} (interval: {message.detection_interval}s)")
            
            return MessageParser.create_response("success", f"Client {message.client_id} registered successfully")
        
        except Exception as e:
            logger.error(f"Error registering client {message.client_id}: {str(e)}")
            return MessageParser.create_response("error", f"Registration failed: {str(e)}")

    def _handle_game_update(self, message: GameUpdateMessage) -> ServerResponseMessage:
        """Handle game state update from client."""
        try:
            # Update game state directly - no enhancement needed as client sends detection_interval
            self.game_state_service.update_game_state(message)
            
            logger.info(f"🎯 Game state updated - Client: {message.client_id}, Window: {message.window_name}, Interval: {message.detection_interval}s")
            
            # Notify client-specific callbacks first (more efficient)
            self._notify_client_update_callbacks(message.client_id, message.window_name)
            
            # Notify global callbacks (for main view)
            self._notify_global_update_callbacks()
            
            return MessageParser.create_response("success", "Game state updated")
        
        except Exception as e:
            logger.error(f"Error updating game state for {message.client_id}: {str(e)}")
            return MessageParser.create_response("error", f"Update failed: {str(e)}")

    def _handle_table_removal(self, message: TableRemovalMessage) -> ServerResponseMessage:
        """Handle table removal from client."""
        try:
            # Remove windows from game state
            removed_count = 0
            for window_name in message.removed_windows:
                if self.game_state_service.remove_client_window(message.client_id, window_name):
                    removed_count += 1
            
            logger.info(f"🗑️ Removed {removed_count}/{len(message.removed_windows)} tables - Client: {message.client_id}")
            
            # Notify callbacks of state change
            self._notify_global_update_callbacks()
            
            return MessageParser.create_response("success", f"Removed {removed_count} tables")
        
        except Exception as e:
            logger.error(f"Error removing tables for {message.client_id}: {str(e)}")
            return MessageParser.create_response("error", f"Removal failed: {str(e)}")

    def _notify_update_callbacks(self) -> None:
        """Notify all registered callbacks that game state has updated (legacy method)."""
        self._notify_global_update_callbacks()
    
    def _notify_global_update_callbacks(self) -> None:
        """Notify global callbacks with all clients data."""
        try:
            # Get current state data
            current_state = self.game_state_service.get_all_game_states()
            
            # Prepare notification data in the format expected by web clients
            notification_data = {
                'type': 'detection_update',
                'detections': current_state['detections'],
                'last_update': current_state['last_update']
            }
            
            # Call all registered global callbacks
            for callback in self.global_update_callbacks:
                try:
                    callback(notification_data)
                except Exception as e:
                    logger.error(f"Error in global update callback: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error notifying global update callbacks: {str(e)}")
    
    def _notify_client_update_callbacks(self, client_id: str, window_name: str) -> None:
        """Notify client-specific callbacks with targeted data."""
        try:
            # Get only this client's data (efficient)
            client_games = self.game_state_service.get_client_game_states(client_id)
            
            if not client_games:
                logger.warning(f"No data found for client {client_id}")
                return
            
            # Detection interval now comes directly from client messages - no enhancement needed
            
            # Find the latest update time for this client
            latest_update_str = None
            for game in client_games:
                game_update = game.get('last_update')
                if game_update and (latest_update_str is None or game_update > latest_update_str):
                    latest_update_str = game_update
            
            # Get detection interval from first game (all games from same client have same interval)
            client_detection_interval = client_games[0].get('detection_interval', 3) if client_games else 3
            
            # Prepare client-specific notification data
            client_data = {
                'type': 'client_detection_update',
                'client_id': client_id,
                'window_name': window_name,
                'detections': client_games,
                'last_update': latest_update_str if latest_update_str else datetime.now().isoformat(),
                'total_tables': len(client_games),
                'detection_interval': client_detection_interval  # Include interval in client data
            }
            
            # Call all registered client-specific callbacks
            for callback in self.client_update_callbacks:
                try:
                    callback(client_id, window_name, client_data)
                except Exception as e:
                    logger.error(f"Error in client update callback for {client_id}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error notifying client update callbacks for {client_id}: {str(e)}")

    def handle_client_disconnect(self, client_id: str) -> None:
        """Handle client disconnection."""
        try:
            self.game_state_service.disconnect_client(client_id)
            # Remove the client's detection interval from tracking
            self.client_detection_intervals.pop(client_id, None)
            logger.info(f"🔌 Client disconnected: {client_id}")
            
            # Notify global callbacks of state change (main view needs to update)
            self._notify_global_update_callbacks()
        
        except Exception as e:
            logger.error(f"Error handling client disconnect {client_id}: {str(e)}")

    def get_current_state(self) -> dict:
        """Get current aggregated game state for immediate response to new web clients."""
        # Detection intervals are now included directly from client messages
        return self.game_state_service.get_all_game_states()

    def get_connected_clients(self) -> list[str]:
        """Get list of currently connected client IDs."""
        return self.game_state_service.get_connected_clients()
    
    def get_client_detection_intervals(self) -> dict[str, int]:
        """Get detection intervals for all connected clients."""
        return self.client_detection_intervals.copy()
    
    def get_average_detection_interval(self) -> int:
        """Get average detection interval across all connected clients."""
        if not self.client_detection_intervals:
            return 3  # Default fallback matching client default (.env.default)
        return int(sum(self.client_detection_intervals.values()) / len(self.client_detection_intervals))
