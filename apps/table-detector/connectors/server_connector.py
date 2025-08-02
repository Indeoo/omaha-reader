import json
import time
import threading
from typing import Optional, Callable, List, Dict, Union
from dataclasses import dataclass
import requests
from datetime import datetime
from loguru import logger

try:
    import socketio
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False
    logger.warning("python-socketio not installed. WebSocket connector will not be available.")

from shared.protocol.message_protocol import (
    GameUpdateMessage, 
    ClientRegistrationMessage
)


@dataclass
class ServerConfig:
    """Configuration for a single server connection."""
    url: str
    connector_type: str = 'auto'  # 'http', 'websocket', 'auto'
    timeout: int = 10
    retry_attempts: int = 3
    retry_delay: int = 5
    priority: int = 1  # Lower number = higher priority for failover
    enabled: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.connector_type not in ['http', 'websocket', 'auto']:
            raise ValueError(f"Invalid connector_type: {self.connector_type}")
        if self.priority < 1:
            raise ValueError("Priority must be >= 1")
        if self.timeout <= 0:
            raise ValueError("Timeout must be > 0")
        if self.retry_attempts < 0:
            raise ValueError("Retry attempts must be >= 0")
        if self.retry_delay < 0:
            raise ValueError("Retry delay must be >= 0")
    
    @classmethod
    def from_url(cls, url: str, **kwargs) -> 'ServerConfig':
        """Create ServerConfig from URL string with optional overrides."""
        return cls(url=url, **kwargs)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'url': self.url,
            'connector_type': self.connector_type,
            'timeout': self.timeout,
            'retry_attempts': self.retry_attempts,
            'retry_delay': self.retry_delay,
            'priority': self.priority,
            'enabled': self.enabled
        }


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
    """WebSocket-based server connector for real-time bidirectional communication."""
    
    def __init__(self, server_url: str, timeout: int = 10, retry_attempts: int = 3, retry_delay: int = 5):
        if not SOCKETIO_AVAILABLE:
            raise ImportError("python-socketio is required for WebSocket connector. Install with: pip install python-socketio")
        
        self.server_url = server_url.rstrip('/')
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        
        # Initialize SocketIO client
        self.sio = socketio.Client(
            logger=False,
            engineio_logger=False,
            reconnection=True,
            reconnection_attempts=retry_attempts,
            reconnection_delay=retry_delay
        )
        
        self.connected = False
        self.client_id = None
        self.connection_lock = threading.Lock()
        self.response_handlers: dict[str, Callable] = {}
        
        # Setup event handlers
        self._setup_event_handlers()
        
        logger.info(f"🔗 WebSocket connector initialized: {self.server_url}")

    def _setup_event_handlers(self):
        """Setup SocketIO event handlers."""
        
        @self.sio.event
        def connect():
            with self.connection_lock:
                self.connected = True
            logger.info("✅ WebSocket connected to server")

        @self.sio.event
        def disconnect():
            with self.connection_lock:
                self.connected = False
            logger.info("🔌 WebSocket disconnected from server")

        @self.sio.event
        def connect_error(data):
            logger.error(f"❌ WebSocket connection error: {data}")

        @self.sio.event
        def register_response(data):
            logger.info(f"📝 Registration response: {data}")
            if 'register_response' in self.response_handlers:
                self.response_handlers['register_response'](data)

        @self.sio.event
        def update_response(data):
            logger.debug(f"🔄 Update response: {data}")
            if 'update_response' in self.response_handlers:
                self.response_handlers['update_response'](data)

        @self.sio.event
        def server_message(data):
            logger.info(f"📨 Server message: {data}")

    def connect(self) -> bool:
        """Connect to WebSocket server."""
        try:
            logger.info(f"🔗 Connecting to WebSocket server: {self.server_url}")
            
            # Attempt connection with retries
            for attempt in range(1, self.retry_attempts + 1):
                try:
                    self.sio.connect(self.server_url, wait_timeout=self.timeout)
                    
                    # Wait for connection to be established
                    time.sleep(1)
                    
                    with self.connection_lock:
                        if self.connected:
                            logger.info(f"✅ WebSocket connection established on attempt {attempt}")
                            return True
                    
                    logger.warning(f"Connection attempt {attempt} failed - not connected")
                    
                except Exception as e:
                    logger.warning(f"Connection attempt {attempt}/{self.retry_attempts} failed: {str(e)}")
                    
                    if attempt < self.retry_attempts:
                        logger.info(f"⏳ Retrying connection in {self.retry_delay} seconds...")
                        time.sleep(self.retry_delay)
            
            logger.error(f"❌ Failed to connect after {self.retry_attempts} attempts")
            return False
            
        except Exception as e:
            logger.error(f"❌ WebSocket connection error: {str(e)}")
            return False

    def register_client(self, client_id: str) -> bool:
        """Register client with server via WebSocket."""
        if not self.is_connected():
            logger.error("❌ Cannot register - not connected to server")
            return False
        
        try:
            self.client_id = client_id
            registration_data = {
                'type': 'client_register',
                'client_id': client_id,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"📝 Registering client via WebSocket: {client_id}")
            
            # Setup response handler
            registration_success = threading.Event()
            registration_result = {'success': False}
            
            def handle_registration_response(data):
                registration_result['success'] = data.get('status') == 'success'
                registration_result['message'] = data.get('message', '')
                registration_success.set()
            
            self.response_handlers['register_response'] = handle_registration_response
            
            # Send registration
            self.sio.emit('client_register', registration_data)
            
            # Wait for response
            if registration_success.wait(timeout=self.timeout):
                success = registration_result['success']
                if success:
                    logger.info(f"✅ Client registered successfully via WebSocket: {client_id}")
                else:
                    logger.error(f"❌ Registration failed: {registration_result.get('message', 'Unknown error')}")
                return success
            else:
                logger.error("❌ Registration timeout - no response from server")
                return False
                
        except Exception as e:
            logger.error(f"❌ WebSocket registration error: {str(e)}")
            return False
        finally:
            # Clean up response handler
            self.response_handlers.pop('register_response', None)

    def send_game_update(self, game_update: GameUpdateMessage) -> bool:
        """Send game update via WebSocket."""
        if not self.is_connected():
            logger.error("❌ Cannot send update - not connected to server")
            return False
        
        try:
            update_data = game_update.to_dict()
            
            # Setup response handler for acknowledgment
            update_success = threading.Event()
            update_result = {'success': False}
            
            def handle_update_response(data):
                update_result['success'] = data.get('status') == 'success'
                update_result['message'] = data.get('message', '')
                update_success.set()
            
            self.response_handlers['update_response'] = handle_update_response
            
            # Send update
            self.sio.emit('game_update', update_data)
            
            # Wait for acknowledgment (with shorter timeout for game updates)
            if update_success.wait(timeout=min(self.timeout, 5)):
                success = update_result['success']
                if not success:
                    logger.error(f"❌ Game update rejected: {update_result.get('message', 'Unknown error')}")
                return success
            else:
                # Don't log timeout errors for game updates as they're frequent
                # and server might not always send acknowledgments
                return True  # Assume success if no explicit failure
                
        except Exception as e:
            logger.error(f"❌ WebSocket game update error: {str(e)}")
            return False
        finally:
            # Clean up response handler
            self.response_handlers.pop('update_response', None)

    def send_message(self, event: str, data: dict) -> bool:
        """Send custom message via WebSocket."""
        if not self.is_connected():
            logger.error("❌ Cannot send message - not connected to server")
            return False
        
        try:
            self.sio.emit(event, data)
            logger.debug(f"📤 Sent WebSocket message: {event}")
            return True
        except Exception as e:
            logger.error(f"❌ WebSocket send message error: {str(e)}")
            return False

    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        with self.connection_lock:
            return self.connected and self.sio.connected

    def wait_for_connection(self, timeout: int = 30) -> bool:
        """Wait for WebSocket connection to be established."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_connected():
                return True
            time.sleep(0.1)
        return False

    def get_server_status(self) -> Optional[dict]:
        """Get server status via WebSocket."""
        if not self.is_connected():
            logger.error("❌ Cannot get status - not connected to server")
            return None
        
        try:
            # Request status via WebSocket
            status_response = threading.Event()
            status_data = {'result': None}
            
            def handle_status_response(data):
                status_data['result'] = data
                status_response.set()
            
            # Setup temporary handler
            self.response_handlers['status_response'] = handle_status_response
            
            # Send status request
            self.sio.emit('get_status', {})
            
            # Wait for response
            if status_response.wait(timeout=self.timeout):
                return status_data['result']
            else:
                logger.error("❌ Status request timeout")
                return None
                
        except Exception as e:
            logger.error(f"❌ WebSocket status error: {str(e)}")
            return None
        finally:
            self.response_handlers.pop('status_response', None)

    def disconnect(self):
        """Disconnect from WebSocket server."""
        try:
            if self.sio.connected:
                logger.info("🔌 Disconnecting from WebSocket server...")
                self.sio.disconnect()
                
                # Wait for disconnection
                timeout = 5
                start_time = time.time()
                while self.sio.connected and (time.time() - start_time) < timeout:
                    time.sleep(0.1)
                
                if not self.sio.connected:
                    logger.info("✅ WebSocket disconnected successfully")
                else:
                    logger.warning("⚠️ WebSocket disconnect timeout")
            
            with self.connection_lock:
                self.connected = False
                
        except Exception as e:
            logger.error(f"❌ WebSocket disconnect error: {str(e)}")

    def close(self):
        """Close WebSocket connection and cleanup."""
        self.disconnect()
        self.response_handlers.clear()
        logger.info("🔌 WebSocket connector closed")


class ServerConnectorManager:
    """Manages multiple server connections with failover and health monitoring."""
    
    def __init__(self, server_configs: List[ServerConfig]):
        """Initialize with list of server configurations."""
        if not server_configs:
            raise ValueError("At least one server configuration is required")
        
        self.server_configs = sorted(server_configs, key=lambda x: x.priority)
        self.connectors: Dict[str, Union[ServerConnector, WebSocketServerConnector]] = {}
        self.connection_status: Dict[str, bool] = {}
        self.last_health_check: Dict[str, datetime] = {}
        self.health_check_interval = 60  # seconds
        
        logger.info(f"🔗 ServerConnectorManager initialized with {len(server_configs)} servers")
        for config in self.server_configs:
            logger.info(f"   - {config.url} ({config.connector_type}, priority: {config.priority})")
    
    def connect_all_servers(self) -> Dict[str, bool]:
        """Connect to all enabled servers."""
        results = {}
        
        for config in self.server_configs:
            if not config.enabled:
                logger.info(f"⏭️ Skipping disabled server: {config.url}")
                continue
            
            connector = self._create_connector(config)
            if connector is None:
                results[config.url] = False
                continue
            
            self.connectors[config.url] = connector
            
            # Test connection
            success = self._test_server_connection(config, connector)
            results[config.url] = success
            self.connection_status[config.url] = success
            self.last_health_check[config.url] = datetime.now()
            
            if success:
                logger.info(f"✅ Connected to server: {config.url}")
            else:
                logger.error(f"❌ Failed to connect to server: {config.url}")
        
        connected_count = sum(results.values())
        logger.info(f"🔗 Connected to {connected_count}/{len(results)} servers")
        
        return results
    
    def register_with_all_servers(self, client_id: str) -> Dict[str, bool]:
        """Register client with all connected servers."""
        results = {}
        
        for url, connector in self.connectors.items():
            if not self.connection_status.get(url, False):
                logger.warning(f"⏭️ Skipping registration with disconnected server: {url}")
                results[url] = False
                continue
            
            try:
                success = connector.register_client(client_id)
                results[url] = success
                
                if success:
                    logger.info(f"✅ Registered with server: {url}")
                else:
                    logger.error(f"❌ Registration failed with server: {url}")
                    self.connection_status[url] = False
                    
            except Exception as e:
                logger.error(f"❌ Registration error with {url}: {str(e)}")
                results[url] = False
                self.connection_status[url] = False
        
        successful_registrations = sum(results.values())
        logger.info(f"📝 Registered with {successful_registrations}/{len(results)} servers")
        
        return results
    
    def send_to_all_servers(self, game_update: GameUpdateMessage) -> Dict[str, bool]:
        """Send game update to all healthy servers."""
        results = {}
        
        # Check if health checks are needed
        self._perform_health_checks_if_needed()
        
        healthy_servers = self.get_healthy_connectors()
        if not healthy_servers:
            logger.error("❌ No healthy servers available for game update")
            return results
        
        for url, connector in healthy_servers.items():
            try:
                success = connector.send_game_update(game_update)
                results[url] = success
                
                if not success:
                    logger.warning(f"⚠️ Game update failed for server: {url}")
                    self.connection_status[url] = False
                    
            except Exception as e:
                logger.error(f"❌ Game update error with {url}: {str(e)}")
                results[url] = False
                self.connection_status[url] = False
        
        successful_sends = sum(results.values())
        if successful_sends > 0:
            logger.debug(f"📤 Game update sent to {successful_sends}/{len(results)} servers")
        else:
            logger.error(f"❌ Game update failed for all servers")
        
        return results
    
    def get_healthy_connectors(self) -> Dict[str, Union[ServerConnector, WebSocketServerConnector]]:
        """Get dictionary of healthy server connectors."""
        healthy = {}
        for url, connector in self.connectors.items():
            if self.connection_status.get(url, False):
                healthy[url] = connector
        return healthy
    
    def get_server_status(self) -> Dict[str, Dict]:
        """Get status of all servers."""
        status = {}
        for config in self.server_configs:
            url = config.url
            status[url] = {
                'config': config.to_dict(),
                'connected': self.connection_status.get(url, False),
                'last_health_check': self.last_health_check.get(url),
                'connector_available': url in self.connectors
            }
        return status
    
    def reconnect_failed_servers(self) -> Dict[str, bool]:
        """Attempt to reconnect to failed servers."""
        results = {}
        
        for config in self.server_configs:
            if not config.enabled:
                continue
                
            url = config.url
            if self.connection_status.get(url, False):
                continue  # Already connected
            
            logger.info(f"🔄 Attempting to reconnect to: {url}")
            
            if url not in self.connectors:
                # Create new connector
                connector = self._create_connector(config)
                if connector is None:
                    results[url] = False
                    continue
                self.connectors[url] = connector
            
            connector = self.connectors[url]
            success = self._test_server_connection(config, connector)
            results[url] = success
            self.connection_status[url] = success
            self.last_health_check[url] = datetime.now()
            
            if success:
                logger.info(f"✅ Reconnected to server: {url}")
            else:
                logger.warning(f"❌ Reconnection failed for server: {url}")
        
        return results
    
    def close_all_connections(self):
        """Close all server connections."""
        logger.info("🔌 Closing all server connections...")
        
        for url, connector in self.connectors.items():
            try:
                connector.close()
                logger.info(f"✅ Closed connection to: {url}")
            except Exception as e:
                logger.error(f"❌ Error closing connection to {url}: {str(e)}")
        
        self.connectors.clear()
        self.connection_status.clear()
        self.last_health_check.clear()
        
        logger.info("🔌 All connections closed")
    
    def _create_connector(self, config: ServerConfig) -> Optional[Union[ServerConnector, WebSocketServerConnector]]:
        """Create connector for server configuration."""
        try:
            return ServerConnectorFactory.create_connector(
                server_url=config.url,
                connector_type=config.connector_type,
                timeout=config.timeout,
                retry_attempts=config.retry_attempts,
                retry_delay=config.retry_delay
            )
        except Exception as e:
            logger.error(f"❌ Failed to create connector for {config.url}: {str(e)}")
            return None
    
    def _test_server_connection(self, config: ServerConfig, connector) -> bool:
        """Test connection to a server."""
        try:
            if hasattr(connector, 'connect'):  # WebSocket connector
                return connector.connect()
            else:  # HTTP connector
                return connector.test_connection()
        except Exception as e:
            logger.error(f"❌ Connection test failed for {config.url}: {str(e)}")
            return False
    
    def _perform_health_checks_if_needed(self):
        """Perform health checks if enough time has passed."""
        current_time = datetime.now()
        
        for url in list(self.connection_status.keys()):
            last_check = self.last_health_check.get(url)
            if last_check is None:
                continue
            
            time_since_check = (current_time - last_check).total_seconds()
            if time_since_check >= self.health_check_interval:
                self._perform_health_check(url)
    
    def _perform_health_check(self, url: str):
        """Perform health check for specific server."""
        if url not in self.connectors:
            return
        
        connector = self.connectors[url]
        config = next((c for c in self.server_configs if c.url == url), None)
        if config is None:
            return
        
        try:
            is_healthy = self._test_server_connection(config, connector)
            self.connection_status[url] = is_healthy
            self.last_health_check[url] = datetime.now()
            
            if not is_healthy and self.connection_status.get(url, True):
                logger.warning(f"⚠️ Health check failed for server: {url}")
            elif is_healthy and not self.connection_status.get(url, False):
                logger.info(f"✅ Server recovered: {url}")
                
        except Exception as e:
            logger.error(f"❌ Health check error for {url}: {str(e)}")
            self.connection_status[url] = False
            self.last_health_check[url] = datetime.now()


class ServerConnectorFactory:
    """Factory class to create appropriate server connector based on URL and preferences."""
    
    @staticmethod
    def create_connector(server_url: str, connector_type: str = 'auto', **kwargs) -> Optional['ServerConnector | WebSocketServerConnector']:
        """
        Create server connector based on type preference.
        
        Args:
            server_url: Server URL to connect to
            connector_type: 'http', 'websocket', or 'auto' (default)
            **kwargs: Additional arguments passed to connector constructor
            
        Returns:
            ServerConnector or WebSocketServerConnector instance, or None if creation fails
        """
        connector_type = connector_type.lower()
        
        if connector_type == 'http':
            return ServerConnectorFactory._create_http_connector(server_url, **kwargs)
        elif connector_type == 'websocket':
            return ServerConnectorFactory._create_websocket_connector(server_url, **kwargs)
        elif connector_type == 'auto':
            return ServerConnectorFactory._create_auto_connector(server_url, **kwargs)
        else:
            logger.error(f"❌ Unknown connector type: {connector_type}")
            return None
    
    @staticmethod
    def _create_http_connector(server_url: str, **kwargs) -> ServerConnector:
        """Create HTTP-based connector."""
        logger.info("🔗 Creating HTTP server connector")
        return ServerConnector(server_url, **kwargs)
    
    @staticmethod
    def _create_websocket_connector(server_url: str, **kwargs) -> Optional[WebSocketServerConnector]:
        """Create WebSocket-based connector."""
        if not SOCKETIO_AVAILABLE:
            logger.error("❌ WebSocket connector requested but python-socketio not available")
            logger.info("💡 Install with: pip install python-socketio")
            return None
        
        logger.info("🔗 Creating WebSocket server connector")
        return WebSocketServerConnector(server_url, **kwargs)
    
    @staticmethod
    def _create_auto_connector(server_url: str, **kwargs) -> 'ServerConnector | WebSocketServerConnector':
        """
        Auto-select connector type based on availability and preferences.
        Prefers WebSocket if available, falls back to HTTP.
        """
        if SOCKETIO_AVAILABLE:
            logger.info("🔗 Auto-selecting WebSocket connector (python-socketio available)")
            return WebSocketServerConnector(server_url, **kwargs)
        else:
            logger.info("🔗 Auto-selecting HTTP connector (python-socketio not available)")
            return ServerConnector(server_url, **kwargs)
    
    @staticmethod
    def test_both_connectors(server_url: str, **kwargs) -> dict:
        """
        Test both HTTP and WebSocket connectors and return results.
        Useful for diagnostics and connector selection.
        """
        results = {
            'http': {'available': True, 'connected': False, 'error': None},
            'websocket': {'available': SOCKETIO_AVAILABLE, 'connected': False, 'error': None}
        }
        
        # Test HTTP connector
        try:
            http_connector = ServerConnector(server_url, **kwargs)
            results['http']['connected'] = http_connector.test_connection()
            http_connector.close()
        except Exception as e:
            results['http']['error'] = str(e)
        
        # Test WebSocket connector if available
        if SOCKETIO_AVAILABLE:
            try:
                ws_connector = WebSocketServerConnector(server_url, **kwargs)
                results['websocket']['connected'] = ws_connector.connect()
                if results['websocket']['connected']:
                    ws_connector.disconnect()
                ws_connector.close()
            except Exception as e:
                results['websocket']['error'] = str(e)
        
        return results