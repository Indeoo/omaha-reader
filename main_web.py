#!/usr/bin/env python3
"""
Web-based version of the poker card detector with Server-Sent Events (SSE).
Shows detected cards on a web page with real-time updates via SSE.
Cards can be copied to clipboard by clicking.
"""
import os
import threading
import time
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, Response
from flask_cors import CORS
from queue import Queue
import uuid

from src.utils.capture_utils import capture_and_save_windows
from src.utils.shared_processing import PokerGameProcessor, format_results_to_games

app = Flask(__name__)
CORS(app)

# Global variables to store the latest detection results
latest_results = {
    'timestamp': None,
    'detections': [],  # This will now be a list of Game instances
    'last_update': None
}

# SSE client management
sse_clients = {}  # {client_id: queue}
sse_lock = threading.Lock()

# Configuration
WAIT_TIME = 5
DEBUG_MODE = True  # Set to False for live capture


def add_sse_client():
    """Add a new SSE client and return client ID and queue"""
    client_id = str(uuid.uuid4())
    client_queue = Queue()

    with sse_lock:
        sse_clients[client_id] = client_queue

    return client_id, client_queue


def remove_sse_client(client_id):
    """Remove an SSE client"""
    with sse_lock:
        if client_id in sse_clients:
            del sse_clients[client_id]


def broadcast_to_sse_clients(data):
    """Broadcast data to all connected SSE clients"""
    message = f"data: {json.dumps(data)}\n\n"

    with sse_lock:
        # Remove disconnected clients
        disconnected_clients = []

        for client_id, queue in sse_clients.items():
            try:
                queue.put(message, block=False)
            except:
                disconnected_clients.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            del sse_clients[client_id]

    if sse_clients:
        print(f"📡 Broadcasted to {len(sse_clients)} SSE clients")


def has_detection_changed(new_games, old_games):
    """Check if detection results have actually changed"""
    if len(new_games) != len(old_games):
        return True

    for new_game, old_game in zip(new_games, old_games):
        if (new_game.player_cards_string != old_game.player_cards_string or
                new_game.table_cards_string != old_game.table_cards_string):
            return True

    return False


def detection_worker():
    """Background worker that continuously captures and detects cards"""
    global latest_results

    # Initialize poker game processor with templates
    poker_game_processor = PokerGameProcessor(
        player_templates_dir="resources/templates/player_cards/",
        table_templates_dir="resources/templates/table_cards/",
        position_templates_dir="resources/templates/positions/",
        detect_positions=False,  # Web version doesn't need positions
        save_result_images=False,  # Don't save result images in web mode
        write_detection_files=False  # Don't write files in web mode
    )

    previous_games = []

    while True:
        try:
            session_timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")

            if DEBUG_MODE:
                # Debug mode - use existing folder
                timestamp_folder = os.path.join(os.getcwd(),
                                                "Dropbox/data_screenshots/_20250610_023049/_20250610_025342")
            else:
                # Live mode - create new folder
                timestamp_folder = os.path.join(os.getcwd(), f"Dropbox/data_screenshots/{session_timestamp}")

            # Capture windows
            captured_images = capture_and_save_windows(
                timestamp_folder=timestamp_folder,
                save_windows=not DEBUG_MODE,
                debug=DEBUG_MODE
            )

            if len(captured_images) > 1:
                # Process all captured images using shared function
                processed_results = poker_game_processor.process_images(
                    captured_images=captured_images,
                    timestamp_folder=timestamp_folder,
                )

                games = format_results_to_games(processed_results)

                # Check if results have changed
                if has_detection_changed(games, previous_games):
                    # Update global results with Game instances
                    latest_results = {
                        'timestamp': session_timestamp,
                        'detections': games,  # Now a list of Game instances
                        'last_update': datetime.now().isoformat()
                    }

                    # Broadcast to SSE clients
                    sse_data = {
                        'type': 'detection_update',
                        'timestamp': latest_results['timestamp'],
                        'detections': [game.to_dict() for game in games],
                        'last_update': latest_results['last_update']
                    }
                    broadcast_to_sse_clients(sse_data)

                    print(f"🔄 Detection changed - broadcasted update at {latest_results['last_update']}")
                    previous_games = games
                else:
                    print(f"📊 No changes detected - skipping broadcast")
            else:
                print("🚫 No poker tables detected, skipping this cycle")

        except Exception as e:
            print(f"❌ Error in detection worker: {str(e)}")

        # Wait before next capture
        time.sleep(WAIT_TIME)


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/cards')
def get_cards():
    """API endpoint to get latest card detections (fallback for non-SSE clients)"""
    # Convert Game instances to dictionaries for JSON serialization
    serializable_results = {
        'timestamp': latest_results['timestamp'],
        'detections': [game.to_dict() for game in latest_results['detections']],
        'last_update': latest_results['last_update']
    }
    return jsonify(serializable_results)


@app.route('/api/stream')
def sse_stream():
    """Server-Sent Events endpoint for real-time updates"""
    client_id, client_queue = add_sse_client()

    def event_stream():
        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected', 'client_id': client_id})}\n\n"

            # Send current state immediately
            if latest_results['detections']:
                initial_data = {
                    'type': 'detection_update',
                    'timestamp': latest_results['timestamp'],
                    'detections': [game.to_dict() for game in latest_results['detections']],
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
            remove_sse_client(client_id)
            print(f"🔌 SSE client {client_id[:8]} disconnected")

    print(f"🔌 New SSE client connected: {client_id[:8]}")

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
    """API endpoint to get configuration settings"""
    return jsonify({
        'frontend_refresh_interval': 0,  # No polling needed with SSE
        'backend_capture_interval': WAIT_TIME,
        'sse_enabled': True
    })


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'debug_mode': DEBUG_MODE,
        'sse_clients': len(sse_clients),
        'last_update': latest_results['last_update']
    })


if __name__ == "__main__":
    print("🎯 Initializing Web-based Omaha Card Reader with SSE")
    print("------------------------------")

    try:
        # Start the detection worker in a background thread
        worker_thread = threading.Thread(target=detection_worker, daemon=True)
        worker_thread.start()

        print(f"\n✅ Web server starting...")
        print(f"📍 Open http://localhost:5001 in your browser")
        print(f"🔄 Real-time updates via Server-Sent Events")
        print(f"📡 SSE endpoint: http://localhost:5001/api/stream")
        print(f"📋 Click any card to copy to clipboard")
        print(f"🐛 Debug mode: {'ON' if DEBUG_MODE else 'OFF'}")
        print("\nPress Ctrl+C to stop the server\n")

        # Start Flask app
        app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)

    except KeyboardInterrupt:
        print("\n🛑 Stopping web server...")
    except Exception as e:
        print(f"❌ Error: {str(e)}")