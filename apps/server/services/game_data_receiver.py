from typing import Optional, Callable
from loguru import logger
from datetime import datetime

from apps.shared.protocol.message_protocol import (
    GameUpdateMessage, 
    ClientRegistrationMessage, 
    MessageParser,
    ServerResponseMessage
)
from apps.server.services.server_game_state import ServerGameStateService


class GameDataReceiver:
    def __init__(self, game_state_service: ServerGameStateService):
        self.game_state_service = game_state_service
        self.global_update_callbacks: list[Callable] = []
        self.client_update_callbacks: list[Callable] = []

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
            
            # Notify client-specific callbacks first (more efficient)
            self._notify_client_update_callbacks(message.client_id, message.window_name)
            
            # Notify global callbacks (for main view)
            self._notify_global_update_callbacks()
            
            return MessageParser.create_response("success", "Game state updated")
        
        except Exception as e:
            logger.error(f"Error updating game state for {message.client_id}: {str(e)}")
            return MessageParser.create_response("error", f"Update failed: {str(e)}")

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
            
            # Find the latest update time for this client
            latest_update = None
            for game in client_games:
                if 'last_update' in game:
                    game_time = datetime.fromisoformat(game['last_update'].replace('Z', '+00:00'))
                    if latest_update is None or game_time > latest_update:
                        latest_update = game_time
            
            # Prepare client-specific notification data
            client_data = {
                'type': 'client_detection_update',
                'client_id': client_id,
                'window_name': window_name,
                'detections': client_games,
                'last_update': latest_update.isoformat() if latest_update else datetime.now().isoformat(),
                'total_tables': len(client_games)
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
            logger.info(f"🔌 Client disconnected: {client_id}")
            
            # Notify global callbacks of state change (main view needs to update)
            self._notify_global_update_callbacks()
        
        except Exception as e:
            logger.error(f"Error handling client disconnect {client_id}: {str(e)}")

    def get_current_state(self) -> dict:
        """Get current aggregated game state for immediate response to new web clients."""
        return self.game_state_service.get_all_game_states()

    def get_connected_clients(self) -> list[str]:
        """Get list of currently connected client IDs."""
        return self.game_state_service.get_connected_clients()