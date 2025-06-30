#!/usr/bin/env python3

import os
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit


class OmahaWebApi:

    def __init__(self, omaha_engine, show_table_cards=True, show_positions=True, show_moves=True):
        self.omaha_engine = omaha_engine
        self.socketio = None
        self.show_table_cards = show_table_cards
        self.show_positions = show_positions
        self.show_moves = show_moves

        # Register detection service observer
        self.omaha_engine.add_observer(self._on_detection_update)
        self.state_repository = self.omaha_engine.state_repository

    def _on_detection_update(self, data: dict):
        if self.socketio:
            self.socketio.emit('detection_update', data)

    def create_app(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_dir = os.path.abspath(os.path.join(current_dir, '..', '..', 'templates'))

        app = Flask(__name__,
                    template_folder=template_dir,
                    static_folder=os.path.join(template_dir, 'static'))

        CORS(app)

        # Initialize SocketIO
        self.socketio = SocketIO(app, cors_allowed_origins="*")

        self._setup_routes(app)
        self._setup_socketio_events()
        return app

    def _setup_routes(self, app):

        @app.route('/')
        def index():
            return render_template('index.html')

        @app.route('/api/config')
        def get_config():
            return jsonify({
                'backend_capture_interval': getattr(self, 'wait_time', int(os.getenv('WAIT_TIME', '10'))),
                'show_table_cards': self.show_table_cards,
                'show_positions': self.show_positions,
                'show_moves': self.show_moves
            })

        @app.route('/health')
        def health():
            latest_results = self.state_repository.get_latest_results_dict()
            return jsonify({
                'status': 'ok',
                'connected_clients': len(self.socketio.server.manager.rooms.get('/', {})),
                'last_update': latest_results['last_update'],
                'detection_service_available': True,
            })

    def _setup_socketio_events(self):

        @self.socketio.on('connect')
        def handle_connect():
            print(f"🔌 New client connected")

            # Send current state immediately
            latest_results = self.state_repository.get_latest_results_dict()
            if latest_results['detections']:
                emit('detection_update', {
                    'type': 'detection_update',
                    'detections': latest_results['detections'],
                    'last_update': latest_results['last_update']
                })

        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f"🔌 Client disconnected")

    def get_socketio(self):
        return self.socketio