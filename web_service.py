#!/usr/bin/env python3
"""
Web service that handles Flask routes and SSE management.
Separated from detection service for better code organization.
"""
import json
import threading
import uuid
from queue import Queue
from typing import Dict, Optional

from flask import Flask, render_template, jsonify, Response
from flask_cors import CORS


class SSEManager:
    """Manages Server-Sent Events clients and message broadcasting"""

    def __init__(self):
        self._clients: Dict[str, Queue] = {}
        self._lock = threading.Lock()

    def add_client(self) -> tuple[str, Queue]:
        """Add a new SSE client and return client ID and queue"""
        client_id = str(uuid.uuid4())
        client_queue = Queue()

        with self._lock:
            self._clients[client_id] = client_queue

        print(f"🔌 New SSE client connected: {client_id[:8]}")
        return client_id, client_queue

    def remove_client(self, client_id: str):
        """Remove an SSE client"""
        with self._lock:
            if client_id in self._clients:
                del self._clients[client_id]
        print(f"🔌 SSE client {client_id[:8]} disconnected")

    def broadcast(self, data: dict):
        """Broadcast data to all connected SSE clients"""
        message = f"data: {json.dumps(data)}\n\n"

        with self._lock:
            # Remove disconnected clients
            disconnected_clients = []

            for client_id, queue in self._clients.items():
                try:
                    queue.put(message, block=False)
                except:
                    disconnected_clients.append(client_id)

            # Clean up disconnected clients
            for client_id in disconnected_clients:
                del self._clients[client_id]

        if self._clients:
            print(f"📡 Broadcasted to {len(self._clients)} SSE clients")

    def get_client_count(self) -> int:
        """Get the number of connected SSE clients"""
        with self._lock:
            return len(self._clients)


class WebService:
    """Web service that provides Flask routes and handles SSE communication"""

    def __init__(self, detection_service, wait_time: int = 5, debug_mode: bool = True):
        self.detection_service = detection_service
        self.wait_time = wait_time
        self.debug_mode = debug_mode

        # Initialize Flask app
        self.app = Flask(__name__)
        CORS(self.app)

        # Initialize SSE manager
        self.sse_manager = SSEManager()

        # Register detection service observer
        self.detection_service.add_observer(self._on_detection_update)

        # Setup routes
        self._setup_routes()

    def _on_detection_update(self, data: dict):
        """Handle detection updates from detection service"""
        self.sse_manager.broadcast(data)

    def _setup_routes(self):
        """Setup Flask routes"""

        @self.app.route('/')
        def index():
            """Main page"""
            return render_template('index.html')

        @self.app.route('/api/cards')
        def get_cards():
            """API endpoint to get latest card detections (fallback for non-SSE clients)"""
            return jsonify(self.detection_service.get_latest_results())

        @self.app.route('/api/stream')
        def sse_stream():
            """Server-Sent Events endpoint for real-time updates"""
            client_id, client_queue = self.sse_manager.add_client()

            def event_stream():
                try:
                    # Send initial connection message
                    yield f"data: {json.dumps({'type': 'connected', 'client_id': client_id})}\n\n"

                    # Send current state immediately
                    latest_results = self.detection_service.get_latest_results()
                    if latest_results['detections']:
                        initial_data = {
                            'type': 'detection_update',
                            'timestamp': latest_results['timestamp'],
                            'detections': latest_results['detections'],
                            'last_update': latest_results['last_update']
                        }
                        yield f"data: {json.dumps(initial_data)}\n\n"

                    # Stream updates
                    while True:
                        try:
                            # Wait for new message (blocking)
                            message = client_queue.get(timeout=30)  # 30 second timeout for heartbeat
                            yield message
                        except:
                            # Send heartbeat on timeout
                            yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"

                except GeneratorExit:
                    # Client disconnected
                    self.sse_manager.remove_client(client_id)

            return Response(
                event_stream(),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Access-Control-Allow-Origin': '*'
                }
            )

        @self.app.route('/api/config')
        def get_config():
            """API endpoint to get configuration settings"""
            return jsonify({
                'frontend_refresh_interval': 0,  # No polling needed with SSE
                'backend_capture_interval': self.wait_time,
                'sse_enabled': True
            })

        @self.app.route('/health')
        def health():
            """Health check endpoint"""
            latest_results = self.detection_service.get_latest_results()
            return jsonify({
                'status': 'ok',
                'debug_mode': self.debug_mode,
                'sse_clients': self.sse_manager.get_client_count(),
                'last_update': latest_results['last_update'],
                'detection_service_running': self.detection_service.is_running()
            })

    def run(self, host: str = '0.0.0.0', port: int = 5001):
        """Start the Flask web server"""
        print(f"\n✅ Web server starting...")
        print(f"📍 Open http://localhost:{port} in your browser")
        print(f"🔄 Real-time updates via Server-Sent Events")
        print(f"📡 SSE endpoint: http://localhost:{port}/api/stream")
        print(f"📋 Click any card to copy to clipboard")
        print(f"🐛 Debug mode: {'ON' if self.debug_mode else 'OFF'}")
        print("\nPress Ctrl+C to stop the server\n")

        self.app.run(host=host, port=port, debug=False, threaded=True)