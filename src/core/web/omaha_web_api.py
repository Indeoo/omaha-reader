#!/usr/bin/env python3

import json
import os

from flask import Flask, render_template, jsonify, Response
from flask_cors import CORS

from src.core.web.sse_manager import SSEManager


class OmahaWebApi:

    def __init__(self, omaha_engine, sse_manager=None):
        self.omaha_engine = omaha_engine
        self.sse_manager = sse_manager or SSEManager()

        # Register detection service observer
        self.omaha_engine.add_observer(self._on_detection_update)

    def _on_detection_update(self, data: dict):
        self.sse_manager.broadcast(data)

    def create_app(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_dir = os.path.abspath(os.path.join(current_dir, '..', '..', 'templates'))

        app = Flask(__name__,
                    template_folder=template_dir,
                    static_folder=os.path.join(template_dir, 'static'))

        CORS(app)

        self._setup_routes(app)
        return app

    def _setup_routes(self, app):

        @app.route('/')
        def index():
            return render_template('index.html')

        @app.route('/api/stream')
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

        @app.route('/api/config')
        def get_config():
            return jsonify({
                'backend_capture_interval': getattr(self, 'wait_time', 5)
            })

        @app.route('/api/force-detect', methods=['POST'])
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

        @app.route('/health')
        def health():
            latest_results = self.omaha_engine.get_latest_results()
            return jsonify({
                'status': 'ok',
                'sse_clients': self.sse_manager.get_client_count(),
                'last_update': latest_results['last_update'],
                'detection_service_available': True,
            })

    def set_wait_time(self, wait_time: int):
        self.wait_time = wait_time