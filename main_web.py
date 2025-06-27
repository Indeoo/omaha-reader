#!/usr/bin/env python3
"""
Web-based version of the poker card detector with Server-Sent Events (SSE).
Shows detected cards on a web page with real-time updates via SSE.
Cards can be copied to clipboard by clicking.

Refactored version with separated detection and web services.
"""
from detection_service import OmahaGameReader
from web_service import WebService

# Configuration
WAIT_TIME = 3
DEBUG_MODE = True  # Set to False for live capture


def main():
    """Main entry point that orchestrates detection and web services"""
    print("🎯 Initializing Web-based Omaha Card Reader with SSE")
    print("------------------------------")

    try:
        # Initialize detection service
        detection_service = OmahaGameReader(
            wait_time=WAIT_TIME,
            debug_mode=DEBUG_MODE
        )

        # Initialize web service
        web_service = WebService(
            detection_service=detection_service,
            wait_time=WAIT_TIME,
            debug_mode=DEBUG_MODE
        )

        # Start detection service
        detection_service.start()

        # Start web service (this blocks)
        web_service.run(host='0.0.0.0', port=5001)

    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        if 'detection_service' in locals():
            detection_service.stop()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if 'detection_service' in locals():
            detection_service.stop()


if __name__ == "__main__":
    main()