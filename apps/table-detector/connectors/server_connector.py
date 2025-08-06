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
    retry_attempts: int = 3
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
    """Simple HTTP client for sending data to poker servers. No connection state management."""
    
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
        
        logger.info(f"🔗 HTTP connector initialized with {len(self.server_configs)} servers:")
        for config in self.server_configs:
            logger.info(f"   - {config.url} (timeout: {config.timeout}s, retries: {config.retry_attempts})")

    def register_client(self, client_id: str) -> bool:
        """Register client with all servers via HTTP POST."""
        if not self.server_configs:
            logger.warning("No servers configured - skipping registration")
            return False

        message = ClientRegistrationMessage(
            type='client_register',
            client_id=client_id,
            timestamp=datetime.now().isoformat()
        )
        
        successful_registrations = 0
        
        for config in self.server_configs:
            try:
                endpoint = f"{config.url.rstrip('/')}/api/client/register"
                success = self._send_http_request(endpoint, message.to_dict(), config, "registration")
                if success:
                    successful_registrations += 1
                    logger.info(f"✅ Registered with server: {config.url}")
                else:
                    logger.warning(f"⚠️ Registration failed: {config.url}")
            except Exception as e:
                logger.warning(f"⚠️ Registration error for {config.url}: {str(e)}")
        
        if successful_registrations > 0:
            logger.info(f"📝 Registered with {successful_registrations}/{len(self.server_configs)} servers")
            return True
        else:
            logger.warning("⚠️ Failed to register with any server")
            return False

    def send_game_update(self, game_update: GameUpdateMessage) -> bool:
        """Send game update to all servers via HTTP POST."""
        if not self.server_configs:
            logger.debug("No servers configured - skipping game update")
            return False

        successful_sends = 0
        
        for config in self.server_configs:
            try:
                endpoint = f"{config.url.rstrip('/')}/api/client/update"
                success = self._send_http_request(endpoint, game_update.to_dict(), config, "game update")
                if success:
                    successful_sends += 1
            except Exception as e:
                logger.debug(f"Game update failed for {config.url}: {str(e)}")
        
        if successful_sends > 0:
            logger.debug(f"📤 Game update sent to {successful_sends}/{len(self.server_configs)} servers")
            return True
        else:
            logger.debug("Game update failed for all servers")
            return False

    def send_removal_message(self, removal_message) -> bool:
        """Send table removal message to all servers via HTTP POST."""
        if not self.server_configs:
            logger.debug("No servers configured - skipping removal message")
            return False

        successful_sends = 0
        
        for config in self.server_configs:
            try:
                endpoint = f"{config.url.rstrip('/')}/api/client/update"
                success = self._send_http_request(endpoint, removal_message.to_dict(), config, "removal message")
                if success:
                    successful_sends += 1
            except Exception as e:
                logger.debug(f"Removal message failed for {config.url}: {str(e)}")
        
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