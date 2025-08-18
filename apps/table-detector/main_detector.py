import os
import sys
import time
import json
from flask.cli import load_dotenv
from loguru import logger
from typing import List

# Ensure proper path setup for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
apps_dir = os.path.dirname(current_dir)
if apps_dir not in sys.path:
    sys.path.insert(0, apps_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from detection_client import DetectionClient
from connectors.server_connector import SimpleHttpConnector, ServerConfig

load_dotenv()


def parse_server_urls() -> List[str]:
    """Parse server URLs from environment variables."""
    
    # Check for SERVER_URLS first (preferred)
    server_urls_env = os.getenv('SERVER_URLS')
    if not server_urls_env:
        # Fall back to single SERVER_URL
        server_url = os.getenv('SERVER_URL', 'http://localhost:5001')
        return [server_url]
    
    try:
        # Try parsing as JSON array first
        if server_urls_env.startswith('['):
            urls = json.loads(server_urls_env)
        else:
            # Treat as comma-separated URLs
            urls = [url.strip() for url in server_urls_env.split(',') if url.strip()]
        
        # Clean URLs and extract URL strings
        clean_urls = []
        for url in urls:
            if isinstance(url, str):
                clean_url = url.strip().strip('"').strip("'")
                clean_urls.append(clean_url)
            elif isinstance(url, dict) and 'url' in url:
                clean_url = url['url'].strip().strip('"').strip("'")
                clean_urls.append(clean_url)
            else:
                logger.warning(f"⚠️ Invalid server URL format: {url}")
        
        if not clean_urls:
            logger.warning("No valid server URLs found, using default")
            return ['http://localhost:5001']
        
        return clean_urls
                
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"❌ Error parsing server URLs: {str(e)}")
        logger.info("📡 Using default localhost configuration")
        return ['http://localhost:5001']


# Client Configuration  
SERVER_URLS = parse_server_urls()
CLIENT_ID = os.getenv('CLIENT_ID', None)  # Auto-generated if not provided
DETECTION_INTERVAL = int(os.getenv('DETECTION_INTERVAL', '3'))
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
COUNTRY = os.getenv('COUNTRY', "canada").lower()
CONNECTION_TIMEOUT = int(os.getenv('CONNECTION_TIMEOUT', '10'))
RETRY_ATTEMPTS = int(os.getenv('RETRY_ATTEMPTS', '3'))


def main():
    logger.info("🎯 Initializing Omaha Poker Detection Client")
    logger.info(f"🔍 Detection interval: {DETECTION_INTERVAL}s")
    logger.info(f"🐛 Debug mode: {DEBUG_MODE}")
    logger.info(f"🌍 Country: {COUNTRY}")
    
    # Log configured servers
    logger.info(f"🌐 Configured servers ({len(SERVER_URLS)}):")
    for url in SERVER_URLS:
        logger.info(f"   - {url}")

    try:
        # Create simple HTTP connector
        logger.info("🔗 Creating HTTP connector...")
        server_configs = [
            ServerConfig(url=url, timeout=CONNECTION_TIMEOUT, retry_attempts=RETRY_ATTEMPTS)
            for url in SERVER_URLS
        ]
        http_connector = SimpleHttpConnector(server_configs)

        # Initialize detection client
        detection_client = DetectionClient(
            client_id=CLIENT_ID,
            country=COUNTRY,
            debug_mode=DEBUG_MODE,
            detection_interval=DETECTION_INTERVAL,
            server_connector=http_connector
        )

        # Try to register with servers (but continue regardless)
        logger.info("📝 Attempting registration with servers...")
        registration_success = detection_client.register_with_server()
        if registration_success:
            logger.info("✅ Registration successful with at least one server")
        else:
            logger.warning("⚠️ Registration failed, but detection will continue")

        # Start detection (works regardless of server connectivity)
        logger.info("🚀 Starting poker detection...")
        detection_client.start_detection()

        logger.info("✅ Detection client is running!")
        logger.info(f"🔍 Client ID: {detection_client.get_client_id()}")
        logger.info(f"📡 Will attempt to send data to {len(SERVER_URLS)} servers")
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
        
        if 'http_connector' in locals():
            http_connector.close()
        
        logger.info("✅ Client stopped")


if __name__ == "__main__":
    main()