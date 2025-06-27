#!/usr/bin/env python3
"""
Web service that handles Flask routes and SSE management.
Separated from detection service for better code organization.
Updated to work with non-threading OmahaGameReader.
"""
import json
import os

from flask import Flask, render_template, jsonify, Response
from flask_cors import CORS


class WebService:
    """Web service that provides Flask routes and handles SSE communication"""

    def __init__(self, detection_service, wait_time: int = 5, debug_mode: bool = True):
        self.detection_service = detection_service
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
                'backend_capture_interval': self.wait_time
            })

        @self.app.route('/api/detect', methods=['POST'])
        def manual_detect():
            """API endpoint to trigger manual detection"""
            try:
                games = self.detection_service.detect_and_notify()
                return jsonify({
                    'status': 'success',
                    'games_detected': len(games),
                    'message': f'Detected {len(games)} games'
                })
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500

        @self.app.route('/api/force-detect', methods=['POST'])
        def force_detect():
            """API endpoint to force detection (ignore change detection)"""
            try:
                games = self.detection_service.force_detect()
                return jsonify({
                    'status': 'success',
                    'games_detected': len(games),
                    'message': f'Force detected {len(games)} games'
                })
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500

        @self.app.route('/health')
        def health():
            """Health check endpoint"""
            latest_results = self.detection_service.get_latest_results()
            return jsonify({
                'status': 'ok',
                'debug_mode': self.debug_mode,
                'sse_clients': self.sse_manager.get_client_count(),
                'last_update': latest_results['last_update'],
                'detection_service_available': True,  # No longer has is_running()
                'window_hashes': len(self.detection_service.get_window_hash_stats())
            })

    def run(self, host: str = '0.0.0.0', port: int = 5001):
        """Start the Flask web server"""
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