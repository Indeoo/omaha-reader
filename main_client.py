import os
import time
import json
from flask.cli import load_dotenv
from loguru import logger
from typing import List

from src.client.detection_client import DetectionClient
from src.client.connectors.server_connector import ServerConnectorFactory, ServerConnectorManager, ServerConfig

load_dotenv()


def parse_server_configurations() -> List[ServerConfig]:
    """Parse server configurations from environment variables."""
    
    # Check for SERVER_URLS first (preferred)
    server_urls_env = os.getenv('SERVER_URLS')
    if not server_urls_env:
        # Fall back to single SERVER_URL and convert to array
        server_url = os.getenv('SERVER_URL', 'http://localhost:5001')
        server_urls_env = server_url
        logger.info("📡 Converting single SERVER_URL to array format")
    else:
        logger.info("📡 Using SERVER_URLS configuration")
    
    try:
        # Try parsing as JSON array first
        if server_urls_env.startswith('['):
            urls = json.loads(server_urls_env)
        else:
            # Treat as comma-separated URLs or single URL
            urls = [url.strip() for url in server_urls_env.split(',') if url.strip()]
        
        configs = []
        for i, url in enumerate(urls):
            if isinstance(url, str):
                # Simple URL string
                config = ServerConfig.from_url(
                    url=url,
                    connector_type=os.getenv('CONNECTOR_TYPE', 'auto').lower(),
                    timeout=int(os.getenv('CONNECTION_TIMEOUT', '10')),
                    retry_attempts=int(os.getenv('RETRY_ATTEMPTS', '3')),
                    retry_delay=int(os.getenv('RETRY_DELAY', '5')),
                    priority=i + 1  # Order from configuration
                )
            elif isinstance(url, dict):
                # Full configuration object
                config = ServerConfig(
                    url=url.get('url'),
                    connector_type=url.get('connector_type', os.getenv('CONNECTOR_TYPE', 'auto')).lower(),
                    timeout=url.get('timeout', int(os.getenv('CONNECTION_TIMEOUT', '10'))),
                    retry_attempts=url.get('retry_attempts', int(os.getenv('RETRY_ATTEMPTS', '3'))),
                    retry_delay=url.get('retry_delay', int(os.getenv('RETRY_DELAY', '5'))),
                    priority=url.get('priority', i + 1),
                    enabled=url.get('enabled', True)
                )
            else:
                logger.warning(f"⚠️ Invalid server config format: {url}")
                continue
            
            configs.append(config)
        
        if not configs:
            raise ValueError("No valid server configurations found")
        
        return configs
                
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"❌ Error parsing server configuration: {str(e)}")
        # Default fallback
        logger.info("📡 Using default localhost configuration")
        return [ServerConfig.from_url('http://localhost:5001')]


# Client Configuration
SERVER_CONFIGS = parse_server_configurations()
CLIENT_ID = os.getenv('CLIENT_ID', None)  # Auto-generated if not provided
DETECTION_INTERVAL = int(os.getenv('DETECTION_INTERVAL', '10'))
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
COUNTRY = os.getenv('COUNTRY', "canada").lower()


def main():
    logger.info("🎯 Initializing Omaha Poker Detection Client")
    logger.info(f"🔍 Detection interval: {DETECTION_INTERVAL}s")
    logger.info(f"🐛 Debug mode: {DEBUG_MODE}")
    logger.info(f"🌍 Country: {COUNTRY}")
    
    # Log server configurations
    logger.info(f"🌐 Configured servers ({len(SERVER_CONFIGS)}):")
    for config in SERVER_CONFIGS:
        logger.info(f"   - {config.url} ({config.connector_type}, priority: {config.priority})")

    try:
        # Initialize server connector manager
        logger.info("🔗 Creating server connector manager...")
        server_connector_manager = ServerConnectorManager(SERVER_CONFIGS)
        
        # Connect to all servers
        logger.info("🔗 Connecting to all servers...")
        connection_results = server_connector_manager.connect_all_servers()
        
        # Check if at least one server is connected
        successful_connections = sum(connection_results.values())
        if successful_connections == 0:
            logger.error("❌ Cannot connect to any server. Please check:")
            for config in SERVER_CONFIGS:
                logger.error(f"   - Server is running at {config.url}")
            logger.error(f"   - Network connectivity")
            logger.error(f"   - SERVER_URL/SERVER_URLS environment variables")
            return
        
        logger.info(f"✅ Successfully connected to {successful_connections}/{len(SERVER_CONFIGS)} servers")

        # Initialize detection client with connector manager
        detection_client = DetectionClient(
            client_id=CLIENT_ID,
            country=COUNTRY,
            debug_mode=DEBUG_MODE,
            detection_interval=DETECTION_INTERVAL,
            server_connector=server_connector_manager
        )

        # Register client with all servers
        logger.info("📝 Registering with all servers...")
        registration_results = server_connector_manager.register_with_all_servers(detection_client.get_client_id())
        
        successful_registrations = sum(registration_results.values())
        if successful_registrations == 0:
            logger.error("❌ Failed to register with any server")
            return
        
        logger.info(f"✅ Successfully registered with {successful_registrations}/{len(connection_results)} servers")

        # Start detection
        logger.info("🚀 Starting poker detection...")
        detection_client.start_detection()

        logger.info("✅ Client is running!")
        logger.info(f"🔍 Detection client ID: {detection_client.get_client_id()}")
        logger.info(f"📡 Sending data to {successful_connections} servers")
        logger.info(f"⏱️  Detection interval: {DETECTION_INTERVAL} seconds")
        logger.info("\nPress Ctrl+C to stop the client")
        logger.info("-" * 50)

        # Keep client running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n🛑 Stopping client...")

    except Exception as e:
        logger.error(f"❌ Client error: {str(e)}")
        raise
    finally:
        # Clean up
        logger.info("🧹 Cleaning up...")
        
        if 'detection_client' in locals():
            detection_client.stop_detection()
        
        if 'server_connector_manager' in locals():
            server_connector_manager.close_all_connections()
            
        logger.info("✅ Client stopped")


if __name__ == "__main__":
    main()