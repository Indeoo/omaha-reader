import json
import time
from typing import Optional, List
from dataclasses import dataclass
import requests
from datetime import datetime
from loguru import logger

from apps.shared.protocol.message_protocol import (
    GameUpdateMessage, 
    ClientRegistrationMessage
)


@dataclass
class ServerConfig:
    """Simple server configuration for HTTP endpoints."""
    url: str
    timeout: int = 10
    retry_attempts: int = 1
    enabled: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.timeout <= 0:
            raise ValueError("Timeout must be > 0")
        if self.retry_attempts < 0:
            raise ValueError("Retry attempts must be >= 0")
    
    @classmethod
    def from_url(cls, url: str, **kwargs) -> 'ServerConfig':
        """Create ServerConfig from URL string with optional overrides."""
        return cls(url=url, **kwargs)


class SimpleHttpConnector:
    """Simple HTTP client for sending data to poker servers with automatic registration."""
    
    def __init__(self, server_configs: List[ServerConfig]):
        """Initialize with list of server configurations."""
        if not server_configs:
            raise ValueError("At least one server configuration is required")
        
        self.server_configs = [config for config in server_configs if config.enabled]
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'OmahaPokerClient/1.0'
        })
        
        # Track registration status per server URL
        self.registration_status = {config.url: False for config in self.server_configs}
        
        logger.info(f"🔗 HTTP connector initialized with {len(self.server_configs)} servers:")
        for config in self.server_configs:
            logger.info(f"   - {config.url} (timeout: {config.timeout}s, retries: {config.retry_attempts})")

    def _ensure_registration(self, client_id: str, config: ServerConfig) -> bool:
        """Ensure client is registered with a specific server. Returns True if registered."""
        if self.registration_status.get(config.url, False):
            return True  # Already registered
        
        # Attempt registration
        message = ClientRegistrationMessage(
            type='client_register',
            client_id=client_id,
            timestamp=datetime.now().isoformat()
        )
        
        try:
            endpoint = f"{config.url.rstrip('/')}/api/client/register"
            success = self._send_http_request(endpoint, message.to_dict(), config, "registration")
            if success:
                self.registration_status[config.url] = True
                logger.info(f"✅ Registered with server: {config.url}")
                return True
            else:
                logger.debug(f"Registration failed for {config.url}")
                return False
        except Exception as e:
            logger.debug(f"Registration error for {config.url}: {str(e)}")
            return False

    def register_client(self, client_id: str) -> bool:
        """Register client with all servers via HTTP POST (legacy method)."""
        if not self.server_configs:
            logger.warning("No servers configured - skipping registration")
            return False
        
        successful_registrations = 0
        
        for config in self.server_configs:
            if self._ensure_registration(client_id, config):
                successful_registrations += 1
        
        if successful_registrations > 0:
            logger.info(f"📝 Registered with {successful_registrations}/{len(self.server_configs)} servers")
            return True
        else:
            logger.warning("⚠️ Failed to register with any server")
            return False

    def send_game_update(self, game_update: GameUpdateMessage) -> bool:
        """Send game update to all servers via HTTP POST. Ensures registration first."""
        if not self.server_configs:
            logger.debug("No servers configured - skipping game update")
            return False

        successful_sends = 0
        
        for config in self.server_configs:
            try:
                # Ensure registration before sending data
                if not self._ensure_registration(game_update.client_id, config):
                    logger.debug(f"Skipping game update for {config.url} - registration failed")
                    continue
                
                endpoint = f"{config.url.rstrip('/')}/api/client/update"
                success = self._send_http_request(endpoint, game_update.to_dict(), config, "game update")
                if success:
                    successful_sends += 1
                else:
                    # If data send fails, mark as unregistered to retry registration next time
                    self.registration_status[config.url] = False
            except Exception as e:
                logger.debug(f"Game update failed for {config.url}: {str(e)}")
                # If exception occurs, mark as unregistered to retry registration next time
                self.registration_status[config.url] = False
        
        if successful_sends > 0:
            logger.debug(f"📤 Game update sent to {successful_sends}/{len(self.server_configs)} servers")
            return True
        else:
            logger.debug("Game update failed for all servers")
            return False

    def send_removal_message(self, removal_message) -> bool:
        """Send table removal message to all servers via HTTP POST. Ensures registration first."""
        if not self.server_configs:
            logger.debug("No servers configured - skipping removal message")
            return False

        successful_sends = 0
        
        for config in self.server_configs:
            try:
                # Ensure registration before sending data
                if not self._ensure_registration(removal_message.client_id, config):
                    logger.debug(f"Skipping removal message for {config.url} - registration failed")
                    continue
                
                endpoint = f"{config.url.rstrip('/')}/api/client/update"
                success = self._send_http_request(endpoint, removal_message.to_dict(), config, "removal message")
                if success:
                    successful_sends += 1
                else:
                    # If data send fails, mark as unregistered to retry registration next time
                    self.registration_status[config.url] = False
            except Exception as e:
                logger.debug(f"Removal message failed for {config.url}: {str(e)}")
                # If exception occurs, mark as unregistered to retry registration next time
                self.registration_status[config.url] = False
        
        if successful_sends > 0:
            logger.debug(f"📤 Removal message sent to {successful_sends}/{len(self.server_configs)} servers")
            return True
        else:
            logger.debug("Removal message failed for all servers")
            return False

    def _send_http_request(self, endpoint: str, data: dict, config: ServerConfig, operation: str) -> bool:
        """Send HTTP request with simple retry logic."""
        for attempt in range(1, config.retry_attempts + 1):
            try:
                response = self.session.post(
                    endpoint,
                    json=data,
                    timeout=config.timeout
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    if response_data.get('status') == 'success':
                        if attempt > 1:
                            logger.debug(f"✅ {operation} succeeded on attempt {attempt}")
                        return True
                    else:
                        logger.debug(f"Server rejected {operation}: {response_data.get('message', 'Unknown error')}")
                        return False
                else:
                    logger.debug(f"HTTP {response.status_code} for {operation}")
                    
            except requests.exceptions.Timeout:
                logger.debug(f"⏰ Timeout on attempt {attempt}/{config.retry_attempts} for {operation}")
                
            except requests.exceptions.ConnectionError:
                logger.debug(f"🔌 Connection error on attempt {attempt}/{config.retry_attempts} for {operation}")
                
            except requests.exceptions.RequestException as e:
                logger.debug(f"📡 Request error on attempt {attempt}/{config.retry_attempts} for {operation}: {str(e)}")
                
            except Exception as e:
                logger.debug(f"❌ Unexpected error on attempt {attempt}/{config.retry_attempts} for {operation}: {str(e)}")
            
            # Simple backoff for retries
            if attempt < config.retry_attempts:
                delay = min(2 ** (attempt - 1), 5)  # Cap at 5 seconds
                time.sleep(delay)
        
        return False

    def test_connectivity(self) -> dict:
        """Test connectivity to all configured servers."""
        results = {}
        
        for config in self.server_configs:
            try:
                endpoint = f"{config.url.rstrip('/')}/api/clients"
                response = self.session.get(endpoint, timeout=config.timeout)
                results[config.url] = response.status_code == 200
            except Exception:
                results[config.url] = False
        
        return results

    def close(self):
        """Close the HTTP session."""
        if self.session:
            self.session.close()
            logger.debug("🔌 HTTP session closed")


# Factory function to create simple HTTP connector from URLs
def create_http_connector(server_urls: List[str], **kwargs) -> SimpleHttpConnector:
    """Create SimpleHttpConnector from list of server URLs."""
    configs = []
    for url in server_urls:
        config = ServerConfig(url=url, **kwargs)
        configs.append(config)
    
    return SimpleHttpConnector(configs)