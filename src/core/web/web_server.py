#!/usr/bin/env python3
from src.core.web.omaha_web_api import OmahaWebApi


class WebServer:

    def __init__(self, omaha_engine, wait_time: int = 5, debug_mode: bool = True):
        self.omaha_engine = omaha_engine
        self.wait_time = wait_time
        self.debug_mode = debug_mode

        self.app_factory = OmahaWebApi(omaha_engine)
        self.app_factory.set_wait_time(wait_time)
        self.app = self.app_factory.create_app()
        self.socketio = self.app_factory.get_socketio()

    def run(self, host: str = '0.0.0.0', port: int = 5001):
        print(f"\n✅ Web server starting...")
        print(f"📍 Open http://localhost:{port} in your browser")
        print(f"🔄 Real-time updates via WebSocket/SocketIO")
        print(f"🔧 Manual detection: POST to http://localhost:{port}/api/detect")
        print(f"⚡ Force detection: POST to http://localhost:{port}/api/force-detect")
        print(f"📋 Click any card to copy to clipboard")
        print(f"🐛 Debug mode: {'ON' if self.debug_mode else 'OFF'}")
        print("\nPress Ctrl+C to stop the server\n")

        self.socketio.run(self.app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)

    def get_app(self):
        return self.app