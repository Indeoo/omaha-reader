from typing import Optional

from loguru import logger

from apps.server.services.server_game_state import ServerGameStateService
from apps.shared.protocol.message_protocol import ServerResponseMessage, MessageParser, ClientRegistrationMessage, \
    GameUpdateMessage, TableRemovalMessage


class GameDataReceiver:
    def __init__(self, game_state_service: ServerGameStateService):
        self.game_state_service = game_state_service
        self.client_detection_intervals: dict[str, int] = {}  # Track detection intervals per client


    def handle_client_message(self, message_json: str) -> Optional[ServerResponseMessage]:
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
            
            return MessageParser.create_response("success", f"Removed {removed_count} tables")
        
        except Exception as e:
            logger.error(f"Error removing tables for {message.client_id}: {str(e)}")
            return MessageParser.create_response("error", f"Removal failed: {str(e)}")


    def handle_client_disconnect(self, client_id: str) -> None:
        """Handle client disconnection."""
        try:
            self.game_state_service.disconnect_client(client_id)
            # Remove the client's detection interval from tracking
            self.client_detection_intervals.pop(client_id, None)
            logger.info(f"🔌 Client disconnected: {client_id}")
        
        except Exception as e:
            logger.error(f"Error handling client disconnect {client_id}: {str(e)}")

    def get_current_state(self) -> dict:
        """Get current aggregated game state for immediate response to new web clients."""
        # Detection intervals are now included directly from client messages
        return self.game_state_service.get_all_game_states()

    def get_connected_clients(self) -> list[str]:
        """Get list of currently connected client IDs."""
        return self.game_state_service.get_connected_clients()
