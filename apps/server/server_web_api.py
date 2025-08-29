#!/usr/bin/env python3

import os
from datetime import datetime
from pathlib import Path
from functools import wraps

from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from flask_cors import CORS
from loguru import logger

from apps.server.services.game_data_receiver import GameDataReceiver
from apps.server.services.server_game_state import ServerGameStateService
from apps.server.utils.game_data_formatter import format_game_data_for_web


class ServerWebApi:
    def __init__(self, show_table_cards=True, show_positions=True, show_moves=True, show_solver_link=True, require_password=False, password='_test_password_'):
        self.show_table_cards = show_table_cards
        self.show_positions = show_positions
        self.show_moves = show_moves
        self.show_solver_link = show_solver_link
        self.require_password = require_password
        self.password = password
        
        # Initialize server-side services
        self.game_state_service = ServerGameStateService()
        self.game_data_receiver = GameDataReceiver(self.game_state_service)
        
        logger.info("🔄 Server initialized with HTTP polling (WebSocket removed)")

    def create_app(self):
        current_path = Path(__file__).resolve().parent
        template_dir = current_path / "web" / "templates"
        static_dir = current_path / "web" / "templates" / "static"
        
        # Debug logging for Heroku deployment
        logger.info(f"🔍 Current directory: {current_path}")
        logger.info(f"🔍 Template directory: {template_dir}")
        logger.info(f"🔍 Template directory exists: {template_dir.exists()}")
        if template_dir.exists():
            logger.info(f"🔍 Template files: {list(template_dir.iterdir())}")
        logger.info(f"🔍 Static directory: {static_dir}")
        logger.info(f"🔍 Static directory exists: {static_dir.exists()}")

        app = Flask(__name__,
                    template_folder=template_dir,
                    static_folder=static_dir)
        
        # Set secret key for sessions (required for flash messages and session)
        app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

        CORS(app, origins="*")

        # WebSocket removed - using HTTP polling instead
        
        self._setup_routes(app)
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
                    'detections': [format_game_data_for_web(game) for game in client_games],
                    'last_update': latest_update.isoformat() if latest_update else datetime.now().isoformat(),
                    'total_tables': len(client_games)
                })
            except Exception as e:
                logger.error(f"Error getting client data for {client_id}: {str(e)}")
                return jsonify({'error': str(e)}), 500

        @app.route('/api/client/<client_id>/detections')
        def get_client_detections(client_id):
            """API endpoint for polling specific client data (replaces WebSocket subscription)."""
            try:
                import hashlib
                import json
                
                # Get client-specific game state
                client_games = self.game_state_service.get_client_game_states(client_id)
                
                # Generate ETag for this client
                client_json = json.dumps(client_games, sort_keys=True)
                etag = hashlib.md5(client_json.encode()).hexdigest()[:8]
                
                # Check If-None-Match header for 304 response
                if request.headers.get('If-None-Match') == etag:
                    return '', 304  # Not Modified
                
                # Find latest update time
                latest_update = None
                for game in client_games:
                    if 'last_update' in game:
                        game_time = datetime.fromisoformat(game['last_update'].replace('Z', '+00:00'))
                        if latest_update is None or game_time > latest_update:
                            latest_update = game_time
                
                # Prepare response
                response_data = {
                    'type': 'client_detection_update',
                    'client_id': client_id,
                    'detections': [format_game_data_for_web(game) for game in client_games],
                    'last_update': latest_update.isoformat() if latest_update else datetime.now().isoformat(),
                    'total_tables': len(client_games),
                    'polling_interval': 5000
                }
                
                # Create response with ETag
                response = jsonify(response_data)
                response.headers['ETag'] = etag
                response.headers['Cache-Control'] = 'no-cache'
                
                return response
                
            except Exception as e:
                logger.error(f"Error in /api/client/{client_id}/detections: {str(e)}")
                return jsonify({'error': str(e)}), 500

        @app.route('/api/detections')
        def get_detections():
            """API endpoint for polling current game state (replaces WebSocket)."""
            try:
                import hashlib
                import json
                
                # Get current game state
                current_state = self.game_data_receiver.get_current_state()
                
                # Generate ETag for efficient polling
                state_json = json.dumps(current_state, sort_keys=True)
                etag = hashlib.md5(state_json.encode()).hexdigest()[:8]
                
                # Check If-None-Match header for 304 response
                if request.headers.get('If-None-Match') == etag:
                    return '', 304  # Not Modified
                
                # Format detections for web display
                raw_detections = current_state.get('detections', [])
                formatted_detections = [format_game_data_for_web(detection) for detection in raw_detections]
                
                # Prepare response with additional metadata
                response_data = {
                    'type': 'detection_update',
                    'detections': formatted_detections,
                    'last_update': current_state.get('last_update'),
                    'connected_clients': self.game_data_receiver.get_connected_clients(),
                    'total_clients': len(self.game_data_receiver.get_connected_clients()),
                    'polling_interval': 5000  # Suggest 5 second polling
                }
                
                # Create response with ETag
                response = jsonify(response_data)
                response.headers['ETag'] = etag
                response.headers['Cache-Control'] = 'no-cache'
                
                return response
                
            except Exception as e:
                logger.error(f"Error in /api/detections: {str(e)}")
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


    def get_game_data_receiver(self):
        return self.game_data_receiver