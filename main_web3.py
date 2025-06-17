#!/usr/bin/env python3
"""
Web-based version of the poker card detector.
Shows detected cards on a web page with auto-refresh every 20 seconds.
Cards can be copied to clipboard by clicking.
"""
import os
import json
import threading
import time
from datetime import datetime
from flask import Flask, render_template, jsonify
from flask_cors import CORS

from src.utils.capture_utils import capture_and_save_windows
from src.utils.detect_utils import detect_cards_single, detect_positions_single
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
WAIT_TIME = 20
DEBUG_MODE = True  # Set to False for live capture

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


def create_templates_folder():
    """Create templates folder for HTML"""
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    os.makedirs(templates_dir, exist_ok=True)

    # Create index.html
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Poker Card Detector</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #1a1a1a;
            color: #e0e0e0;
            margin: 0;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        h1 {
            text-align: center;
            color: #4CAF50;
            margin-bottom: 30px;
        }

        .status {
            text-align: center;
            margin-bottom: 20px;
            font-size: 14px;
            color: #888;
        }

        .table-container {
            background-color: #2a2a2a;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }

        .table-name {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #4CAF50;
        }

        .cards-section {
            margin-bottom: 15px;
        }

        .cards-label {
            font-size: 14px;
            color: #888;
            margin-bottom: 5px;
        }

        .cards-container {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            align-items: center;
        }

        .cards-block {
            display: flex;
            gap: 3px;
            background-color: #3a3a3a;
            padding: 8px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }

        .cards-block:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
            background-color: #4a4a4a;
        }

        .card {
            background-color: #f0f0f0;
            color: #000;
            padding: 15px 20px;
            border-radius: 6px;
            font-size: 24px;
            font-weight: bold;
            position: relative;
        }

        .card.red {
            color: #d32f2f;
        }

        .card.blue {
            color: #1976d2;
        }

        .card.green {
            color: #1b5e20;
        }

        .card.black {
            color: #000;
        }

        .no-cards {
            color: #666;
            font-style: italic;
        }

        .loading {
            text-align: center;
            padding: 50px;
            font-size: 18px;
            color: #888;
        }

        .error {
            text-align: center;
            padding: 50px;
            font-size: 18px;
            color: #f44336;
        }

        .toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background-color: #4CAF50;
            color: white;
            padding: 15px 20px;
            border-radius: 4px;
            opacity: 0;
            transition: opacity 0.3s ease;
            z-index: 1000;
        }

        .toast.show {
            opacity: 1;
        }

        .refresh-timer {
            position: fixed;
            top: 20px;
            right: 20px;
            background-color: #2a2a2a;
            padding: 10px 15px;
            border-radius: 4px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎰 Poker Card Detector</h1>
        <div class="status" id="status">Waiting for data...</div>
        <div id="content">
            <div class="loading">Loading...</div>
        </div>
    </div>

    <div class="refresh-timer" id="refreshTimer">Next update in: <span id="countdown">20</span>s</div>
    <div class="toast" id="toast">Copied to clipboard!</div>

    <script>
        let countdown = 20;
        let countdownInterval;

        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(() => {
                showToast('Copied to clipboard!');
            }).catch(err => {
                console.error('Failed to copy:', err);
                showToast('Failed to copy!');
            });
        }

        function showToast(message) {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.classList.add('show');
            setTimeout(() => {
                toast.classList.remove('show');
            }, 2000);
        }

        function getSuitColor(card) {
            const suit = card.slice(-1);
            if (suit === '♥') return 'red';
            if (suit === '♦') return 'blue';
            if (suit === '♣') return 'green';
            return 'black'; // spades
        }

        function renderCards(detections) {
            const content = document.getElementById('content');

            if (!detections || detections.length === 0) {
                content.innerHTML = '<div class="error">No tables detected</div>';
                return;
            }

            let html = '';
            detections.forEach((detection, index) => {
                html += `
                    <div class="table-container">
                        <div class="table-name">${detection.window_name}</div>

                        <div class="cards-section">
                            <div class="cards-label">Player Cards:</div>
                            <div class="cards-container">
                `;

                if (detection.player_cards && detection.player_cards.length > 0) {
                    html += `<div class="cards-block" onclick="copyToClipboard('${detection.player_cards_string}')">`;
                    detection.player_cards.forEach(card => {
                        const colorClass = getSuitColor(card.display);
                        html += `<div class="card ${colorClass}">${card.display}</div>`;
                    });
                    html += `</div>`;
                } else {
                    html += '<div class="no-cards">No cards detected</div>';
                }

                html += `
                            </div>
                        </div>

                        <div class="cards-section">
                            <div class="cards-label">Table Cards:</div>
                            <div class="cards-container">
                `;

                if (detection.table_cards && detection.table_cards.length > 0) {
                    html += `<div class="cards-block" onclick="copyToClipboard('${detection.table_cards_string}')">`;
                    detection.table_cards.forEach(card => {
                        const colorClass = getSuitColor(card.display);
                        html += `<div class="card ${colorClass}">${card.display}</div>`;
                    });
                    html += `</div>`;
                } else {
                    html += '<div class="no-cards">No cards detected</div>';
                }

                html += `
                            </div>
                        </div>
                    </div>
                `;
            });

            content.innerHTML = html;
        }

        function updateStatus(lastUpdate) {
            const status = document.getElementById('status');
            if (lastUpdate) {
                const date = new Date(lastUpdate);
                status.textContent = `Last updated: ${date.toLocaleTimeString()}`;
            }
        }

        function startCountdown() {
            countdown = 20;
            clearInterval(countdownInterval);
            countdownInterval = setInterval(() => {
                countdown--;
                document.getElementById('countdown').textContent = countdown;
                if (countdown <= 0) {
                    clearInterval(countdownInterval);
                    fetchCards();
                }
            }, 1000);
        }

        async function fetchCards() {
            try {
                const response = await fetch('/api/cards');
                const data = await response.json();

                updateStatus(data.last_update);
                renderCards(data.detections);
                startCountdown();
            } catch (error) {
                console.error('Error fetching cards:', error);
                document.getElementById('content').innerHTML = '<div class="error">Error loading data</div>';
                startCountdown();
            }
        }

        // Initial load
        fetchCards();
    </script>
</body>
</html>'''

    with open(os.path.join(templates_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html_content)


if __name__ == "__main__":
    print("🎯 Initializing Web-based Omaha Card Reader")
    print("------------------------------")

    try:
        # Load templates
        player_templates = load_templates("resources/templates/player_cards/")
        table_templates = load_templates("resources/templates/table_cards/")
        position_templates = load_templates("resources/templates/positions/")

        # Create templates folder and HTML file
        create_templates_folder()

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