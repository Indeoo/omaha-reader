import os
import atexit

from flask.cli import load_dotenv
from loguru import logger
from apscheduler.schedulers.background import BackgroundScheduler

from apps.server import create_app

load_dotenv()

# Server Configuration
PORT = int(os.getenv('PORT', '5001'))
HOST = os.getenv('HOST', '0.0.0.0')  # Allow external connections
ALLOWED_CLIENTS = os.getenv('ALLOWED_CLIENTS', '*')  # * means allow all
MAX_CLIENTS = int(os.getenv('MAX_CLIENTS', '10'))

# UI Display Configuration 
SHOW_TABLE_CARDS = os.getenv('SHOW_TABLE_CARDS', 'true').lower() == 'true'
SHOW_POSITIONS = os.getenv('SHOW_POSITIONS', 'false').lower() == 'true'
SHOW_MOVES = os.getenv('SHOW_MOVES', 'false').lower() == 'true'
SHOW_SOLVER_LINK = os.getenv('SHOW_SOLVER_LINK', 'true').lower() == 'true'

# Security Configuration
REQUIRE_PASSWORD = os.getenv('REQUIRE_PASSWORD', 'false').lower() == 'true'
PASSWORD = os.getenv('PASSWORD', '_test_password_')


def main():
    logger.info("🌐 Initializing Omaha Poker Server")
    logger.info(f"📡 Server will accept connections from: {ALLOWED_CLIENTS}")
    logger.info(f"👥 Maximum concurrent clients: {MAX_CLIENTS}")

    try:
        app = create_app(
            show_table_cards=SHOW_TABLE_CARDS,
            show_positions=SHOW_POSITIONS,
            show_moves=SHOW_MOVES,
            show_solver_link=SHOW_SOLVER_LINK,
            require_password=REQUIRE_PASSWORD,
            password=PASSWORD
        )

        # Setup periodic cleanup of stale tables
        scheduler = BackgroundScheduler()
        game_state_service = app.extensions["game_state_service"]

        def cleanup_stale_tables():
            result = game_state_service.cleanup_stale_tables(stale_threshold_minutes=1)
            if result['tables_removed'] > 0 or result['clients_removed'] > 0:
                logger.info(
                    f"🧹 Cleanup: removed {result['tables_removed']} stale tables, "
                    f"{result['clients_removed']} empty clients"
                )

        # Run cleanup every 60 seconds (1 minute)
        scheduler.add_job(
            func=cleanup_stale_tables,
            trigger="interval",
            seconds=60,
            id='cleanup_stale_tables'
        )

        scheduler.start()
        atexit.register(lambda: scheduler.shutdown())

        logger.info(f"✅ Server starting on {HOST}:{PORT}")
        logger.info(f"🌍 Web UI will be accessible at http://{HOST}:{PORT}")
        logger.info(f"📡 Client HTTP endpoints:")
        logger.info(f"   - POST http://{HOST}:{PORT}/api/client/update")
        logger.info(f"   - GET  http://{HOST}:{PORT}/api/detections")
        logger.info(f"   - GET  http://{HOST}:{PORT}/api/clients")
        logger.info(f"🔄 Using HTTP polling (5 second interval)")
        logger.info(f"🧹 Stale table cleanup enabled (60 second interval, 5 minute threshold)")
        logger.info("\nPress Ctrl+C to stop the server")
        logger.info("-" * 50)

        # Start server with standard Flask (this blocks)
        app.run(
            host=HOST, 
            port=PORT, 
            debug=False,
            threaded=True  # Enable threading for concurrent requests
        )

    except KeyboardInterrupt:
        logger.info("\n🛑 Stopping server...")
    except Exception as e:
        logger.error(f"❌ Server error: {str(e)}")
        raise
    finally:
        logger.info("✅ Server stopped")


if __name__ == "__main__":
    main()
