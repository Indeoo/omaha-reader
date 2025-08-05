#!/usr/bin/env python3

import os
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from loguru import logger

from services.game_data_receiver import GameDataReceiver
from services.server_game_state import ServerGameStateService


class ServerWebApi:
    def __init__(self, show_table_cards=True, show_positions=True, show_moves=True, show_solver_link=True, require_password=False, password='_test_password_'):
        self.show_table_cards = show_table_cards
        self.show_positions = show_positions
        self.show_moves = show_moves
        self.show_solver_link = show_solver_link
        self.require_password = require_password
        self.password = password
        self.socketio = None
        
        # Initialize server-side services
        self.game_state_service = ServerGameStateService()
        self.game_data_receiver = GameDataReceiver(self.game_state_service)
        
        # Register callbacks to notify web clients when game state updates
        self.game_data_receiver.add_global_update_callback(self._on_global_update)
        self.game_data_receiver.add_client_update_callback(self._on_client_update)

    def _on_global_update(self, data: dict):
        """Called when global game state needs to be broadcast (all clients data)."""
        if self.socketio:
            # Broadcast to all web clients (main view showing all clients)
            self.socketio.emit('detection_update', data)
            logger.info(f"🔄 Global update broadcast: {len(data.get('detections', []))} total games")
    
    def _on_client_update(self, client_id: str, window_name: str, client_data: dict):
        """Called when specific client data is updated (targeted update)."""
        if self.socketio:
            # Send targeted update to client-specific room (O(1) operation)
            self.socketio.emit('client_detection_update', client_data, room=f"client_{client_id}")
            
            # Send incremental update to main view (only the changed client data)
            incremental_data = {
                'type': 'client_data_changed',
                'client_id': client_id,
                'window_name': window_name,
                'client_data': client_data,
                'timestamp': datetime.now().isoformat()
            }
            self.socketio.emit('client_data_changed', incremental_data)
            
            logger.info(f"🎯 Client-specific update: {client_id}/{window_name} → {len(client_data.get('detections', []))} tables")

    def create_app(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_dir = os.path.join(current_dir, "web", "templates")
        static_dir = os.path.join(current_dir, "web", "templates", "static")
        
        # Debug logging for Heroku deployment
        logger.info(f"🔍 Current directory: {current_dir}")
        logger.info(f"🔍 Template directory: {template_dir}")
        logger.info(f"🔍 Template directory exists: {os.path.exists(template_dir)}")
        if os.path.exists(template_dir):
            logger.info(f"🔍 Template files: {os.listdir(template_dir)}")
        logger.info(f"🔍 Static directory: {static_dir}")
        logger.info(f"🔍 Static directory exists: {os.path.exists(static_dir)}")

        app = Flask(__name__,
                    template_folder=template_dir,
                    static_folder=static_dir)
        
        # Set secret key for sessions (required for flash messages and session)
        app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

        CORS(app, origins="*")

        # Initialize SocketIO
        self.socketio = SocketIO(app, cors_allowed_origins="*")

        self._setup_routes(app)
        self._setup_socketio_events()
        self._setup_client_endpoints(app)
        return app

    def _require_auth(self, f):
        """Decorator to require authentication if password protection is enabled."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not self.require_password:
                return f(*args, **kwargs)
            if 'authenticated' not in session or not session['authenticated']:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function

    def _setup_routes(self, app):
        @app.route('/login', methods=['GET', 'POST'])
        def login():
            if not self.require_password:
                return redirect(url_for('index'))
            
            if request.method == 'POST':
                password = request.form.get('password')
                if password == self.password:
                    session['authenticated'] = True
                    return redirect(url_for('index'))
                else:
                    flash('Invalid password')
                    return render_template('login.html', error='Invalid password')
            
            return render_template('login.html')

        @app.route('/')
        @self._require_auth
        def index():
            return render_template('index.html')

        @app.route('/client/<client_id>')
        @self._require_auth
        def client_view(client_id):
            """Individual client view page."""
            # Check if client exists
            connected_clients = self.game_data_receiver.get_connected_clients()
            if client_id not in connected_clients:
                return render_template('index.html', error=f"Client '{client_id}' not found"), 404
            
            return render_template('client.html', client_id=client_id)

        @app.route('/api/config')
        def get_config():
            return jsonify({
                'backend_capture_interval': int(os.getenv('DETECTION_INTERVAL', '10')),
                'show_table_cards': self.show_table_cards,
                'show_positions': self.show_positions,
                'show_moves': self.show_moves,
                'show_solver_link': self.show_solver_link
            })

        @app.route('/api/client/<client_id>/config')
        def get_client_config(client_id):
            """Client-specific configuration."""
            # Check if client exists
            connected_clients = self.game_data_receiver.get_connected_clients()
            if client_id not in connected_clients:
                return jsonify({'error': 'Client not found'}), 404
            
            return jsonify({
                'client_id': client_id,
                'backend_capture_interval': int(os.getenv('DETECTION_INTERVAL', '10')),
                'show_table_cards': self.show_table_cards,
                'show_positions': self.show_positions,
                'show_moves': self.show_moves,
                'show_solver_link': self.show_solver_link
            })

        @app.route('/api/client/<client_id>/data')
        def get_client_data(client_id):
            """Get data for a specific client."""
            try:
                client_games = self.game_state_service.get_client_game_states(client_id)
                latest_update = None
                
                # Find the latest update time
                for game in client_games:
                    if 'last_update' in game:
                        game_time = datetime.fromisoformat(game['last_update'].replace('Z', '+00:00'))
                        if latest_update is None or game_time > latest_update:
                            latest_update = game_time
                
                return jsonify({
                    'client_id': client_id,
                    'detections': client_games,
                    'last_update': latest_update.isoformat() if latest_update else datetime.now().isoformat(),
                    'total_tables': len(client_games)
                })
            except Exception as e:
                logger.error(f"Error getting client data for {client_id}: {str(e)}")
                return jsonify({'error': str(e)}), 500

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
                
                from apps.shared.protocol.message_protocol import ClientRegistrationMessage
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

        @self.socketio.on('subscribe_client')
        def handle_subscribe_client(data):
            """Subscribe to updates for a specific client."""
            try:
                client_id = data.get('client_id')
                if not client_id:
                    emit('subscription_error', {'error': 'client_id required'})
                    return
                
                # Join room for this client
                from flask_socketio import join_room
                join_room(f"client_{client_id}")
                
                # Send current state for this client
                client_games = self.game_state_service.get_client_game_states(client_id)
                latest_update = None
                
                for game in client_games:
                    if 'last_update' in game:
                        game_time = datetime.fromisoformat(game['last_update'].replace('Z', '+00:00'))
                        if latest_update is None or game_time > latest_update:
                            latest_update = game_time
                
                emit('client_detection_update', {
                    'type': 'client_detection_update',
                    'client_id': client_id,
                    'detections': client_games,
                    'last_update': latest_update.isoformat() if latest_update else datetime.now().isoformat()
                })
                
                logger.info(f"📤 Client {client_id} subscription established: {len(client_games)} games")
                
            except Exception as e:
                logger.error(f"Error in client subscription: {str(e)}")
                emit('subscription_error', {'error': str(e)})

        @self.socketio.on('unsubscribe_client')
        def handle_unsubscribe_client(data):
            """Unsubscribe from client updates."""
            try:
                client_id = data.get('client_id')
                if client_id:
                    from flask_socketio import leave_room
                    leave_room(f"client_{client_id}")
                    logger.info(f"📤 Client {client_id} subscription ended")
            except Exception as e:
                logger.error(f"Error in client unsubscription: {str(e)}")

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