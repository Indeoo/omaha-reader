from typing import Optional, Callable
from loguru import logger
from datetime import datetime

from src.core.shared.message_protocol import (
    GameUpdateMessage, 
    ClientRegistrationMessage, 
    MessageParser,
    ServerResponseMessage
)
from src.core.server.server_game_state import ServerGameStateService


class GameDataReceiver:
    def __init__(self, game_state_service: ServerGameStateService):
        self.game_state_service = game_state_service
        self.update_callbacks: list[Callable] = []

    def add_update_callback(self, callback: Callable[[dict], None]) -> None:
        """Add callback to be called when game state updates occur."""
        self.update_callbacks.append(callback)

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
            logger.info(f"✅ Client registered: {message.client_id}")
            
            return MessageParser.create_response("success", f"Client {message.client_id} registered successfully")
        
        except Exception as e:
            logger.error(f"Error registering client {message.client_id}: {str(e)}")
            return MessageParser.create_response("error", f"Registration failed: {str(e)}")

    def _handle_game_update(self, message: GameUpdateMessage) -> ServerResponseMessage:
        """Handle game state update from client."""
        try:
            # Update game state
            self.game_state_service.update_game_state(message)
            
            logger.info(f"🎯 Game state updated - Client: {message.client_id}, Window: {message.window_name}")
            
            # Notify all registered callbacks
            self._notify_update_callbacks()
            
            return MessageParser.create_response("success", "Game state updated")
        
        except Exception as e:
            logger.error(f"Error updating game state for {message.client_id}: {str(e)}")
            return MessageParser.create_response("error", f"Update failed: {str(e)}")

    def _notify_update_callbacks(self) -> None:
        """Notify all registered callbacks that game state has updated."""
        try:
            # Get current state data
            current_state = self.game_state_service.get_all_game_states()
            
            # Prepare notification data in the format expected by web clients
            notification_data = {
                'type': 'detection_update',
                'detections': current_state['detections'],
                'last_update': current_state['last_update']
            }
            
            # Call all registered callbacks
            for callback in self.update_callbacks:
                try:
                    callback(notification_data)
                except Exception as e:
                    logger.error(f"Error in update callback: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error notifying update callbacks: {str(e)}")

    def handle_client_disconnect(self, client_id: str) -> None:
        """Handle client disconnection."""
        try:
            self.game_state_service.disconnect_client(client_id)
            logger.info(f"🔌 Client disconnected: {client_id}")
            
            # Notify callbacks of state change
            self._notify_update_callbacks()
        
        except Exception as e:
            logger.error(f"Error handling client disconnect {client_id}: {str(e)}")

    def get_current_state(self) -> dict:
        """Get current aggregated game state for immediate response to new web clients."""
        return self.game_state_service.get_all_game_states()

    def get_connected_clients(self) -> list[str]:
        """Get list of currently connected client IDs."""
        return self.game_state_service.get_connected_clients()