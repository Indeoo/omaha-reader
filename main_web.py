#!/usr/bin/env python3
"""
Web-based version of the poker card detector with Server-Sent Events (SSE).
Shows detected cards on a web page with real-time updates via SSE.
Cards can be copied to clipboard by clicking.

Refactored version with separated detection and web services.
Uses scheduling instead of internal threading.
"""
from omaha_game import OmahaGameReader
from src.detection_scheduler import DetectionScheduler
from web_service import WebService

# Configuration
WAIT_TIME = 3
DEBUG_MODE = True  # Set to False for live capture


def main():
    """Main entry point that orchestrates detection and web services"""
    print("🎯 Initializing Web-based Omaha Card Reader with SSE")
    print("------------------------------")

    detection_service = None
    scheduler = None
    web_service = None

    try:
        # Initialize detection service (no internal threading)
        detection_service = OmahaGameReader(debug_mode=DEBUG_MODE)

        # Initialize detection scheduler
        scheduler = DetectionScheduler(detection_service, WAIT_TIME)

        # Initialize web service
        web_service = WebService(
            detection_service=detection_service,
            wait_time=WAIT_TIME,
            debug_mode=DEBUG_MODE
        )

        # Start detection scheduler
        scheduler.start()

        # Start web service (this blocks)
        web_service.run(host='0.0.0.0', port=5001)

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