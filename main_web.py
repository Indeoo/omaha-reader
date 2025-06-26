#!/usr/bin/env python3
"""
Web-based version of the poker card detector.
Shows detected cards on a web page with auto-refresh every 20 seconds.
Cards can be copied to clipboard by clicking.
"""
import os
import threading
import time
from datetime import datetime
from flask import Flask, render_template, jsonify
from flask_cors import CORS

from src.domain.game import Game
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

# Configuration
WAIT_TIME = 5
DEBUG_MODE = True  # Set to False for live capture


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

    while True:
        try:
            session_timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")

            if DEBUG_MODE:
                # Debug mode - use existing folder
                timestamp_folder = os.path.join(os.getcwd(), "Dropbox/data_screenshots/_20250610_023049/_20250610_025342")
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
                processed_results = poker_game_processor.process_captured_images(
                    captured_images=captured_images,
                    timestamp_folder=timestamp_folder,
                )

                games = format_results_to_games(processed_results)

                # Update global results with Game instances
                latest_results = {
                    'timestamp': session_timestamp,
                    'detections': games,  # Now a list of Game instances
                    'last_update': datetime.now().isoformat()
                }

                print(f"Updated results at {latest_results['last_update']}")
            else:
                print("No poker board detected, skip this timestamp")

        except Exception as e:
            print(f"Error in detection worker: {str(e)}")

        # Wait before next capture
        time.sleep(WAIT_TIME)


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/cards')
def get_cards():
    """API endpoint to get latest card detections"""
    # Convert Game instances to dictionaries for JSON serialization
    serializable_results = {
        'timestamp': latest_results['timestamp'],
        'detections': [game.to_dict() for game in latest_results['detections']],
        'last_update': latest_results['last_update']
    }
    return jsonify(serializable_results)


@app.route('/api/config')
def get_config():
    """API endpoint to get configuration settings"""
    return jsonify({
        'frontend_refresh_interval': 5,
        'backend_capture_interval': WAIT_TIME
    })


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'debug_mode': DEBUG_MODE})


if __name__ == "__main__":
    print("🎯 Initializing Web-based Omaha Card Reader")
    print("------------------------------")

    try:
        # Start the detection worker in a background thread
        worker_thread = threading.Thread(target=detection_worker, daemon=True)
        worker_thread.start()

        print(f"\n✅ Web server starting...")
        print(f"📍 Open http://localhost:5001 in your browser")
        print(f"🔄 Auto-refresh every {WAIT_TIME} seconds")
        print(f"📋 Click any card to copy to clipboard")
        print(f"🐛 Debug mode: {'ON' if DEBUG_MODE else 'OFF'}")
        print("\nPress Ctrl+C to stop the server\n")

        # Start Flask app
        app.run(host='0.0.0.0', port=5001, debug=False)

    except KeyboardInterrupt:
        print("\n🛑 Stopping web server...")
    except Exception as e:
        print(f"❌ Error: {str(e)}")