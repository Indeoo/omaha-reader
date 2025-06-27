#!/usr/bin/env python3

import json
import os

from flask import Flask, render_template, jsonify, Response
from flask_cors import CORS

from src.core.service.sse_manager import SSEManager


class WebService:

    def __init__(self, omaha_engine, wait_time: int = 5, debug_mode: bool = True):
        self.omaha_engine = omaha_engine
        self.wait_time = wait_time
        self.debug_mode = debug_mode

        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Navigate to src/templates
        template_dir = os.path.abspath(os.path.join(current_dir, '..', '..', 'templates'))

        # Initialize Flask app
        self.app = Flask(__name__, template_folder=template_dir)
        CORS(self.app)

        # Initialize SSE manager
        self.sse_manager = SSEManager()

        # Register detection service observer
        self.omaha_engine.add_observer(self._on_detection_update)

        # Setup routes
        self._setup_routes()

    def _on_detection_update(self, data: dict):
        self.sse_manager.broadcast(data)

    def _setup_routes(self):

        @self.app.route('/')
        def index():
            return render_template('index.html')

        @self.app.route('/api/stream')
        def sse_stream():
            client_id, client_queue = self.sse_manager.add_client()

            def event_stream():
                try:
                    # Send initial connection message
                    yield f"data: {json.dumps({'type': 'connected', 'client_id': client_id})}\n\n"

                    # Send current state immediately
                    latest_results = self.omaha_engine.get_latest_results()
                    if latest_results['detections']:
                        initial_data = {
                            'type': 'detection_update',
                            'timestamp': latest_results.get('timestamp'),
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
            return jsonify({
                'backend_capture_interval': self.wait_time
            })

        @self.app.route('/api/force-detect', methods=['POST'])
        def force_detect():
            try:
                self.omaha_engine.force_detect()
                return jsonify({
                    'status': 'success',
                })
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500

        @self.app.route('/health')
        def health():
            latest_results = self.omaha_engine.get_latest_results()
            return jsonify({
                'status': 'ok',
                'debug_mode': self.debug_mode,
                'sse_clients': self.sse_manager.get_client_count(),
                'last_update': latest_results['last_update'],
                'detection_service_available': True,  # No longer has is_running()
            })

    def run(self, host: str = '0.0.0.0', port: int = 5001):
        print(f"\n✅ Web server starting...")
        print(f"📍 Open http://localhost:{port} in your browser")
        print(f"🔄 Real-time updates via Server-Sent Events")
        print(f"📡 SSE endpoint: http://localhost:{port}/api/stream")
        print(f"🔧 Manual detection: POST to http://localhost:{port}/api/detect")
        print(f"⚡ Force detection: POST to http://localhost:{port}/api/force-detect")
        print(f"📋 Click any card to copy to clipboard")
        print(f"🐛 Debug mode: {'ON' if self.debug_mode else 'OFF'}")
        print("\nPress Ctrl+C to stop the server\n")

        self.app.run(host=host, port=port, debug=False, threaded=True)