import json
import time
from typing import Optional
import requests
from datetime import datetime
from loguru import logger

from src.core.shared.message_protocol import (
    GameUpdateMessage, 
    ClientRegistrationMessage, 
    MessageParser
)


class ServerConnector:
    def __init__(self, server_url: str, timeout: int = 10, retry_attempts: int = 3, retry_delay: int = 5):
        self.server_url = server_url.rstrip('/')
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        
        # API endpoints
        self.register_endpoint = f"{self.server_url}/api/client/register"
        self.update_endpoint = f"{self.server_url}/api/client/update"
        self.status_endpoint = f"{self.server_url}/api/clients"
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'OmahaPokerClient/1.0'
        })
        
        logger.info(f"🔗 Server connector initialized: {self.server_url}")

    def test_connection(self) -> bool:
        """Test if server is reachable."""
        try:
            response = self.session.get(
                self.status_endpoint, 
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Server connection test successful: {self.server_url}")
                return True
            else:
                logger.error(f"❌ Server connection test failed: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Server connection test failed: {str(e)}")
            return False

    def register_client(self, client_id: str) -> bool:
        """Register client with server."""
        try:
            message = ClientRegistrationMessage(
                type='client_register',
                client_id=client_id,
                timestamp=datetime.now().isoformat()
            )
            
            logger.info(f"📝 Registering client with server: {client_id}")
            
            success = self._send_with_retry(
                self.register_endpoint,
                message.to_dict(),
                f"register client {client_id}"
            )
            
            if success:
                logger.info(f"✅ Client registered successfully: {client_id}")
            else:
                logger.error(f"❌ Client registration failed: {client_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error registering client {client_id}: {str(e)}")
            return False

    def send_game_update(self, game_update: GameUpdateMessage) -> bool:
        """Send game update to server."""
        try:
            return self._send_with_retry(
                self.update_endpoint,
                game_update.to_dict(),
                f"game update for {game_update.window_name}"
            )
            
        except Exception as e:
            logger.error(f"Error sending game update: {str(e)}")
            return False

    def _send_with_retry(self, endpoint: str, data: dict, operation: str) -> bool:
        """Send HTTP request with retry logic."""
        last_error = None
        
        for attempt in range(1, self.retry_attempts + 1):
            try:
                response = self.session.post(
                    endpoint,
                    json=data,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    if response_data.get('status') == 'success':
                        if attempt > 1:
                            logger.info(f"✅ {operation} succeeded on attempt {attempt}")
                        return True
                    else:
                        logger.error(f"Server rejected {operation}: {response_data.get('message', 'Unknown error')}")
                        return False
                else:
                    logger.error(f"HTTP error for {operation}: {response.status_code} - {response.text}")
                    last_error = f"HTTP {response.status_code}"
                    
            except requests.exceptions.Timeout:
                last_error = "Timeout"
                logger.warning(f"⏰ Timeout on attempt {attempt}/{self.retry_attempts} for {operation}")
                
            except requests.exceptions.ConnectionError:
                last_error = "Connection error"
                logger.warning(f"🔌 Connection error on attempt {attempt}/{self.retry_attempts} for {operation}")
                
            except requests.exceptions.RequestException as e:
                last_error = str(e)
                logger.warning(f"📡 Request error on attempt {attempt}/{self.retry_attempts} for {operation}: {str(e)}")
                
            except Exception as e:
                last_error = str(e)
                logger.error(f"❌ Unexpected error on attempt {attempt}/{self.retry_attempts} for {operation}: {str(e)}")
            
            # Wait before retry (except on last attempt)
            if attempt < self.retry_attempts:
                logger.info(f"⏳ Retrying {operation} in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
        
        logger.error(f"❌ Failed to {operation} after {self.retry_attempts} attempts. Last error: {last_error}")
        return False

    def get_server_status(self) -> Optional[dict]:
        """Get server status and connected clients."""
        try:
            response = self.session.get(
                self.status_endpoint,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get server status: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting server status: {str(e)}")
            return None

    def close(self):
        """Close the session."""
        if self.session:
            self.session.close()
            logger.info("🔌 Server connector session closed")


class WebSocketServerConnector:
    """Alternative WebSocket-based server connector (for future use)."""
    
    def __init__(self, websocket_url: str):
        self.websocket_url = websocket_url
        self.ws = None
        logger.info(f"🔗 WebSocket connector initialized: {websocket_url}")
        # WebSocket implementation would go here
        # This is a placeholder for future WebSocket implementation
        
    def connect(self) -> bool:
        """Connect to WebSocket server."""
        # TODO: Implement WebSocket connection
        logger.warning("WebSocket connector not yet implemented - use HTTP connector")
        return False
        
    def send_message(self, message: str) -> bool:
        """Send message via WebSocket."""
        # TODO: Implement WebSocket message sending  
        logger.warning("WebSocket message sending not yet implemented")
        return False
        
    def disconnect(self):
        """Disconnect from WebSocket server."""
        # TODO: Implement WebSocket disconnection
        pass