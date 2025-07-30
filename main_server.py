import os
from flask.cli import load_dotenv
from loguru import logger

from src.core.server.server_web_api import ServerWebApi

load_dotenv()

# Server Configuration
PORT = int(os.getenv('PORT', '5001'))
HOST = os.getenv('HOST', '0.0.0.0')  # Allow external connections
ALLOWED_CLIENTS = os.getenv('ALLOWED_CLIENTS', '*')  # * means allow all
MAX_CLIENTS = int(os.getenv('MAX_CLIENTS', '10'))

# UI Display Configuration 
SHOW_TABLE_CARDS = os.getenv('SHOW_TABLE_CARDS', 'true').lower() == 'true'
SHOW_POSITIONS = os.getenv('SHOW_POSITIONS', 'true').lower() == 'true'
SHOW_MOVES = os.getenv('SHOW_MOVES', 'true').lower() == 'true'
SHOW_SOLVER_LINK = os.getenv('SHOW_SOLVER_LINK', 'true').lower() == 'true'


def main():
    logger.info("🌐 Initializing Omaha Poker Server")
    logger.info(f"📡 Server will accept connections from: {ALLOWED_CLIENTS}")
    logger.info(f"👥 Maximum concurrent clients: {MAX_CLIENTS}")

    try:
        # Initialize server web API
        server_api = ServerWebApi(
            show_table_cards=SHOW_TABLE_CARDS,
            show_positions=SHOW_POSITIONS,
            show_moves=SHOW_MOVES,
            show_solver_link=SHOW_SOLVER_LINK
        )
        
        app = server_api.create_app()
        socketio = server_api.get_socketio()

        logger.info(f"✅ Server starting on {HOST}:{PORT}")
        logger.info(f"🌍 Web UI will be accessible at http://{HOST}:{PORT}")
        logger.info(f"🔌 WebSocket endpoint: ws://{HOST}:{PORT}/socket.io/")
        logger.info(f"📡 Client HTTP endpoints:")
        logger.info(f"   - POST http://{HOST}:{PORT}/api/client/register")
        logger.info(f"   - POST http://{HOST}:{PORT}/api/client/update")
        logger.info(f"   - GET  http://{HOST}:{PORT}/api/clients")
        logger.info("\nPress Ctrl+C to stop the server")
        logger.info("-" * 50)

        # Start server (this blocks)
        socketio.run(
            app, 
            host=HOST, 
            port=PORT, 
            debug=False, 
            allow_unsafe_werkzeug=True, 
            use_reloader=False, 
            log_output=True
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