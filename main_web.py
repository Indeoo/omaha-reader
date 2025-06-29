#!/usr/bin/env python3

from src.core.service.detection_scheduler import DetectionScheduler
from src.core.omaha_engine import OmahaEngine
from src.core.web.web_server import WebServer

# Configuration
WAIT_TIME = 10
DEBUG_MODE = True  # Set to False for live capture


def main():
    print("🎯 Initializing Web-based Omaha Card Reader with SSE")
    print("------------------------------")

    scheduler = None

    try:
        # Initialize detection service (no internal threading)
        omaha_engine = OmahaEngine(debug_mode=DEBUG_MODE)

        # Initialize detection scheduler
        scheduler = DetectionScheduler(omaha_engine, WAIT_TIME)

        # Initialize web service
        web_server = WebServer(
            omaha_engine=omaha_engine,
            wait_time=WAIT_TIME,
            debug_mode=DEBUG_MODE
        )

        # Start detection scheduler
        scheduler.start()

        # Start web service (this blocks)
        web_server.run(host='0.0.0.0', port=5001)

    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        # Clean up
        if scheduler:
            scheduler.stop()
        print("✅ All services stopped")


if __name__ == "__main__":
    main()