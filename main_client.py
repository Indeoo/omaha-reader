import os
import time
from flask.cli import load_dotenv
from loguru import logger

from src.core.client.detection_client import DetectionClient
from src.core.client.server_connector import ServerConnector

load_dotenv()

# Client Configuration
SERVER_URL = os.getenv('SERVER_URL', 'http://localhost:5003')
CLIENT_ID = os.getenv('CLIENT_ID', None)  # Auto-generated if not provided
DETECTION_INTERVAL = int(os.getenv('DETECTION_INTERVAL', '10'))
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
COUNTRY = os.getenv('COUNTRY', "canada").lower()

# Connection Configuration
CONNECTION_TIMEOUT = int(os.getenv('CONNECTION_TIMEOUT', '10'))
RETRY_ATTEMPTS = int(os.getenv('RETRY_ATTEMPTS', '3'))
RETRY_DELAY = int(os.getenv('RETRY_DELAY', '5'))


def main():
    logger.info("🎯 Initializing Omaha Poker Detection Client")
    logger.info(f"🌐 Server URL: {SERVER_URL}")
    logger.info(f"🔍 Detection interval: {DETECTION_INTERVAL}s")
    logger.info(f"🐛 Debug mode: {DEBUG_MODE}")
    logger.info(f"🌍 Country: {COUNTRY}")

    try:
        # Initialize server connector
        logger.info("🔗 Connecting to server...")
        server_connector = ServerConnector(
            server_url=SERVER_URL,
            timeout=CONNECTION_TIMEOUT,
            retry_attempts=RETRY_ATTEMPTS,
            retry_delay=RETRY_DELAY
        )

        # Test server connection
        if not server_connector.test_connection():
            logger.error("❌ Cannot connect to server. Please check:")
            logger.error(f"   - Server is running at {SERVER_URL}")
            logger.error(f"   - Network connectivity")
            logger.error(f"   - SERVER_URL environment variable")
            return

        # Initialize detection client
        detection_client = DetectionClient(
            client_id=CLIENT_ID,
            country=COUNTRY,
            debug_mode=DEBUG_MODE,
            detection_interval=DETECTION_INTERVAL,
            server_connector=server_connector
        )

        # Register client with server
        logger.info("📝 Registering with server...")
        if not detection_client.register_with_server():
            logger.error("❌ Failed to register with server")
            return

        # Start detection
        logger.info("🚀 Starting poker detection...")
        detection_client.start_detection()

        logger.info("✅ Client is running!")
        logger.info(f"🔍 Detection client ID: {detection_client.get_client_id()}")
        logger.info(f"📡 Sending data to: {SERVER_URL}")
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
        
        if 'server_connector' in locals():
            server_connector.close()
            
        logger.info("✅ Client stopped")


if __name__ == "__main__":
    main()