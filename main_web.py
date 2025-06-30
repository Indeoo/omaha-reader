#!/usr/bin/env python3

from src.core.omaha_engine import OmahaEngine
from src.core.web.web_server import WebServer

# Configuration
WAIT_TIME = 10
DEBUG_MODE = True  # Set to False for live capture


def main():
    print("🎯 Initializing Web-based Omaha Card Reader with SSE")
    print("------------------------------")

    omaha_engine = None

    try:
        # Initialize detection service with scheduling built-in
        omaha_engine = OmahaEngine(debug_mode=DEBUG_MODE, detection_interval=WAIT_TIME)

        # Initialize web service
        web_server = WebServer(omaha_engine=omaha_engine, wait_time=WAIT_TIME, debug_mode=DEBUG_MODE)

        # Start scheduled detection
        omaha_engine.start_scheduler()

        # Start web service (this blocks)
        web_server.run(host='0.0.0.0', port=5001)

    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        # Clean up
        if omaha_engine:
            omaha_engine.stop_scheduler()
        print("✅ All services stopped")


if __name__ == "__main__":
    main()