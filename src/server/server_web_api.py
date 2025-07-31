#!/usr/bin/env python3

import os
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from loguru import logger

from src.server.services.game_data_receiver import GameDataReceiver
from src.server.services.server_game_state import ServerGameStateService


class ServerWebApi:
    def __init__(self, show_table_cards=True, show_positions=True, show_moves=True, show_solver_link=True):
        self.show_table_cards = show_table_cards
        self.show_positions = show_positions
        self.show_moves = show_moves
        self.show_solver_link = show_solver_link
        self.socketio = None
        
        # Initialize server-side services
        self.game_state_service = ServerGameStateService()
        self.game_data_receiver = GameDataReceiver(self.game_state_service)
        
        # Register callback to notify web clients when game state updates
        self.game_data_receiver.add_update_callback(self._on_game_state_update)

    def _on_game_state_update(self, data: dict):
        """Called when game state is updated from client."""
        if self.socketio:
            self.socketio.emit('detection_update', data)
            logger.info(f"🔄 Broadcasted update to web clients: {len(data.get('detections', []))} games")

    def create_app(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_dir = os.path.abspath(os.path.join(current_dir, '..', '..', '..', 'src', 'templates'))

        app = Flask(__name__,
                    template_folder="../web/templates",
                    static_folder="../web/templates/static")

        CORS(app, origins="*")

        # Initialize SocketIO
        self.socketio = SocketIO(app, cors_allowed_origins="*")

        self._setup_routes(app)
        self._setup_socketio_events()
        self._setup_client_endpoints(app)
        return app

    def _setup_routes(self, app):
        @app.route('/')
        def index():
            return render_template('index.html')

        @app.route('/api/config')
        def get_config():
            return jsonify({
                'backend_capture_interval': int(os.getenv('DETECTION_INTERVAL', '10')),
                'show_table_cards': self.show_table_cards,
                'show_positions': self.show_positions,
                'show_moves': self.show_moves,
                'show_solver_link': self.show_solver_link
            })

        @app.route('/api/clients')
        def get_connected_clients():
            """API endpoint to see connected detection clients."""
            return jsonify({
                'connected_clients': self.game_data_receiver.get_connected_clients(),
                'total_clients': len(self.game_data_receiver.get_connected_clients())
            })

    def _setup_client_endpoints(self, app):
        """Endpoints for detection clients to send data."""
        
        @app.route('/api/client/register', methods=['POST'])
        def register_client():
            """HTTP endpoint for client registration."""
            try:
                data = request.get_json()
                if not data or 'client_id' not in data:
                    return jsonify({'error': 'client_id required'}), 400
                
                from src.shared.protocol.message_protocol import ClientRegistrationMessage
                from datetime import datetime
                
                message = ClientRegistrationMessage(
                    type='client_register',
                    client_id=data['client_id'],
                    timestamp=datetime.now().isoformat()
                )
                
                response = self.game_data_receiver.handle_client_message(message.to_json())
                
                if response and response.status == 'success':
                    return jsonify({'status': 'success', 'message': response.message})
                else:
                    return jsonify({'status': 'error', 'message': response.message if response else 'Unknown error'}), 500
                    
            except Exception as e:
                logger.error(f"Error in client registration: {str(e)}")
                return jsonify({'error': str(e)}), 500

        @app.route('/api/client/update', methods=['POST'])
        def update_game_state():
            """HTTP endpoint for game state updates."""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'JSON data required'}), 400
                
                import json
                response = self.game_data_receiver.handle_client_message(json.dumps(data))
                
                if response and response.status == 'success':
                    return jsonify({'status': 'success', 'message': response.message})
                else:
                    return jsonify({'status': 'error', 'message': response.message if response else 'Unknown error'}), 500
                    
            except Exception as e:
                logger.error(f"Error in game state update: {str(e)}")
                return jsonify({'error': str(e)}), 500

    def _setup_socketio_events(self):
        @self.socketio.on('connect')
        def handle_web_client_connect():
            logger.info(f"🔌 New web client connected")

            # Send current state immediately to new web client
            current_state = self.game_data_receiver.get_current_state()
            if current_state['detections']:
                emit('detection_update', {
                    'type': 'detection_update',
                    'detections': current_state['detections'],
                    'last_update': current_state['last_update']
                })
                logger.info(f"📤 Sent current state to new web client: {len(current_state['detections'])} games")

        @self.socketio.on('disconnect')
        def handle_web_client_disconnect():
            logger.info(f"🔌 Web client disconnected")

        @self.socketio.on('client_register')
        def handle_client_register_ws(data):
            """WebSocket endpoint for client registration."""
            try:
                import json
                response = self.game_data_receiver.handle_client_message(json.dumps(data))
                emit('register_response', response.to_dict() if response else {'status': 'error', 'message': 'Unknown error'})
            except Exception as e:
                logger.error(f"WebSocket client registration error: {str(e)}")
                emit('register_response', {'status': 'error', 'message': str(e)})

        @self.socketio.on('game_update')
        def handle_game_update_ws(data):
            """WebSocket endpoint for game updates."""
            try:
                import json
                response = self.game_data_receiver.handle_client_message(json.dumps(data))
                emit('update_response', response.to_dict() if response else {'status': 'error', 'message': 'Unknown error'})
            except Exception as e:
                logger.error(f"WebSocket game update error: {str(e)}")
                emit('update_response', {'status': 'error', 'message': str(e)})

    def get_socketio(self):
        return self.socketio

    def get_game_data_receiver(self):
        return self.game_data_receiver