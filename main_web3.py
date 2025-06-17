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

from src.utils.capture_utils import capture_and_save_windows
from src.utils.detect_utils import detect_cards_single
from src.utils.opencv_utils import load_templates
from src.domain.readed_card import ReadedCard

app = Flask(__name__)
CORS(app)

# Global variables to store the latest detection results
latest_results = {
    'timestamp': None,
    'detections': [],
    'last_update': None
}

# Configuration
WAIT_TIME = 10
DEBUG_MODE = False  # Set to False for live capture

# Templates (loaded once)
player_templates = None
table_templates = None
position_templates = None


def detection_worker():
    """Background worker that continuously captures and detects cards"""
    global latest_results

    while True:
        try:
            session_timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")

            if DEBUG_MODE:
                # Debug mode - use existing folder
                timestamp_folder = os.path.join(os.getcwd(), "_20250610_023049/_20250610_025342")
            else:
                # Live mode - create new folder
                timestamp_folder = os.path.join(os.getcwd(), f"Dropbox/data_screenshots/{session_timestamp}")
                os.makedirs(timestamp_folder, exist_ok=True)

            # Capture windows
            captured_images = capture_and_save_windows(
                timestamp_folder=timestamp_folder,
                save_windows=not DEBUG_MODE,
                debug=DEBUG_MODE
            )

            # Process each captured image
            detections = []
            for i, captured_item in enumerate(captured_images):
                window_name = captured_item['window_name']

                # Skip full screen captures
                if window_name == 'full_screen':
                    continue

                # Detect cards
                card_result = detect_cards_single(captured_item, i, player_templates, table_templates)

                if card_result:
                    # Format the cards for display
                    player_cards = card_result.get('player_cards_raw', [])
                    table_cards = card_result.get('table_cards_raw', [])

                    detection = {
                        'window_name': window_name,
                        'player_cards': format_cards_for_web(player_cards),
                        'table_cards': format_cards_for_web(table_cards),
                        'player_cards_string': ReadedCard.format_cards(player_cards),
                        'table_cards_string': ReadedCard.format_cards(table_cards)
                    }

                    if detection['player_cards'] or detection['table_cards']:
                        detections.append(detection)

            # Update global results
            latest_results = {
                'timestamp': session_timestamp,
                'detections': detections,
                'last_update': datetime.now().isoformat()
            }

            print(f"Updated results at {latest_results['last_update']}")

        except Exception as e:
            print(f"Error in detection worker: {str(e)}")

        # Wait before next capture
        time.sleep(WAIT_TIME)


def format_cards_for_web(cards):
    """Format cards for web display with suit symbols"""
    if not cards:
        return []

    formatted = []
    for card in cards:
        if card.template_name:
            formatted.append({
                'name': card.template_name,
                'display': format_card_with_unicode(card.template_name),
                'score': round(card.match_score, 3) if card.match_score else 0
            })
    return formatted


def format_card_with_unicode(card_name):
    """Convert card name to include Unicode suit symbols"""
    if not card_name or len(card_name) < 2:
        return card_name

    # Unicode suit symbols mapping
    suit_unicode = {
        'S': '♠',  # Spades
        'H': '♥',  # Hearts
        'D': '♦',  # Diamonds
        'C': '♣'  # Clubs
    }

    # Get the last character as suit
    suit = card_name[-1].upper()
    rank = card_name[:-1]

    if suit in suit_unicode:
        return f"{rank}{suit_unicode[suit]}"
    else:
        return card_name


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/cards')
def get_cards():
    """API endpoint to get latest card detections"""
    return jsonify(latest_results)


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'debug_mode': DEBUG_MODE})


if __name__ == "__main__":
    print("🎯 Initializing Web-based Omaha Card Reader")
    print("------------------------------")

    try:
        # Load templates
        player_templates = load_templates("resources/templates/player_cards/")
        table_templates = load_templates("resources/templates/table_cards/")
        position_templates = load_templates("resources/templates/positions/")

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