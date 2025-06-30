from src.core.web.omaha_web_api import OmahaWebApi
from src.core.omaha_engine import OmahaEngine

# Configuration
WAIT_TIME = 10
DEBUG_MODE = True


def main():
    print("🎯 Initializing Web-based Omaha Card Reader")

    try:
        # Initialize omaha engine
        omaha_engine = OmahaEngine(debug_mode=DEBUG_MODE, detection_interval=WAIT_TIME)

        # Initialize web service (keep OmahaWebApi separate)
        app_factory = OmahaWebApi(omaha_engine=omaha_engine)
        app = app_factory.create_app()
        socketio = app_factory.get_socketio()

        # Start detection scheduler
        omaha_engine.start_scheduler()

        print(f"✅ Web server starting...")
        print(f"📍 Open http://localhost:5001 in your browser")
        print("\nPress Ctrl+C to stop the server\n")

        # Start web service (this blocks)
        socketio.run(app, host='0.0.0.0', port=5001, debug=False, allow_unsafe_werkzeug=True)

    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        # Clean up
        if 'omaha_engine' in locals():
            omaha_engine.stop_scheduler()
        print("✅ All services stopped")


if __name__ == "__main__":
    main()