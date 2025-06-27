#!/usr/bin/env python3
"""
Game state manager that handles game state tracking and change detection.
Extracted from DetectionService for better separation of concerns.
"""
import threading
from datetime import datetime
from typing import List

from src.core.domain.detection_result import DetectionResult
from src.core.domain.game import Game
from src.core.reader.player_move_reader import PlayerMoveReader
from src.core.utils.opencv_utils import load_templates, pil_to_cv2


class GameStateManager:
    """
    Manages game state and detects changes between detection cycles.
    Handles conversion between DetectionResult and Game objects.
    """

    def __init__(self):
        # State management
        self._latest_results = {
            'timestamp': None,
            'detections': [],  # List of Game instances
            'last_update': None
        }
        self._state_lock = threading.Lock()
        self._previous_games = []

        # Initialize player move reader
        self._player_move_reader = None
        self._init_player_move_reader()

    def _init_player_move_reader(self):
        """Initialize the player move reader with templates"""
        try:
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
            move_templates_dir = os.path.join(project_root, "resources", "templates", "turn_options")

            if os.path.exists(move_templates_dir):
                move_templates = load_templates(move_templates_dir)
                if move_templates:
                    self._player_move_reader = PlayerMoveReader(move_templates)
                    print(f"✅ PlayerMoveReader initialized with {len(move_templates)} templates")
                else:
                    print("⚠️ No turn option templates found")
            else:
                print(f"⚠️ Turn options template directory not found: {move_templates_dir}")
        except Exception as e:
            print(f"❌ Error initializing PlayerMoveReader: {str(e)}")

    def is_move(self, captured_image) -> bool:
        """
        Check if it's the player's turn to move by detecting move option buttons

        Args:
            captured_image: CapturedImage object to check

        Returns:
            True if move options are detected, False otherwise
        """
        if not self._player_move_reader:
            return False

        try:
            # Convert PIL image to OpenCV format
            cv2_image = pil_to_cv2(captured_image.image)

            # Read move options
            detected_moves = self._player_move_reader.read(cv2_image)

            # Log the result
            if detected_moves:
                move_types = [move.move_type for move in detected_moves]
                print(f"🎯 Player's move detected! Options: {', '.join(move_types)}")
                return True
            else:
                print(f"⏸️ Not player's move - no action buttons detected")
                return False

        except Exception as e:
            print(f"❌ Error checking player move: {str(e)}")
            return False

    def update_state(self, processed_results: List[DetectionResult], timestamp_folder: str) -> bool:
        """
        Update game state with new detection results.

        Args:
            processed_results: List of DetectionResult objects from detection
            timestamp_folder: Timestamp folder path for tracking

        Returns:
            True if state changed and observers should be notified, False otherwise
        """
        # Convert results to games
        new_games = self._convert_results_to_games(processed_results)

        # Check if results have changed
        has_changed = self._has_detection_changed(new_games, self._previous_games)

        # Check player move status for each game
        for i, (game, result) in enumerate(zip(new_games, processed_results)):
            is_player_move = self.is_move(result.captured_image)
            # You can store this information in the game object if needed
            # For now, just logging it
            if is_player_move:
                print(f"  ↳ Table '{game.window_name}' - IT'S YOUR TURN!")

        if has_changed:
            # Update state with Game instances
            with self._state_lock:
                self._latest_results = {
                    'timestamp': timestamp_folder.split('/')[-1],  # Extract timestamp from path
                    'detections': new_games,  # Store Game instances
                    'last_update': datetime.now().isoformat()
                }

            # Update previous games for next comparison
            self._previous_games = new_games

        return has_changed

    def get_latest_results(self) -> dict:
        """
        Get the latest detection results (thread-safe)

        Returns:
            Dictionary with timestamp, detections, and last_update
        """
        with self._state_lock:
            # Convert Game instances to dictionaries for JSON serialization
            return {
                'timestamp': self._latest_results['timestamp'],
                'detections': [game.to_dict() for game in self._latest_results['detections']],
                'last_update': self._latest_results['last_update']
            }

    def get_notification_data(self) -> dict:
        """
        Get data formatted for observer notifications

        Returns:
            Dictionary formatted for notifying observers
        """
        with self._state_lock:
            return {
                'type': 'detection_update',
                'timestamp': self._latest_results['timestamp'],
                'detections': [game.to_dict() for game in self._latest_results['detections']],
                'last_update': self._latest_results['last_update']
            }

    def _convert_results_to_games(self, processed_results: List[DetectionResult]) -> List[Game]:
        """
        Convert DetectionResult objects to Game instances

        Args:
            processed_results: List of DetectionResult objects

        Returns:
            List of Game instances
        """
        games = []

        for result in processed_results:
            if result.has_cards or result.has_positions:  # Include games with positions
                # Create game with raw ReadedCard objects and positions
                game = Game(
                    window_name=result.window_name,
                    player_cards=result.player_cards,
                    table_cards=result.table_cards,
                    positions=result.positions
                )
                games.append(game)

        return games

    def _has_detection_changed(self, new_games: List[Game], old_games: List[Game]) -> bool:
        """
        Check if detection results have actually changed

        Args:
            new_games: Current game states
            old_games: Previous game states

        Returns:
            True if changes detected, False otherwise
        """
        if len(new_games) != len(old_games):
            return True

        for new_game, old_game in zip(new_games, old_games):
            if (new_game.get_player_cards_string() != old_game.get_player_cards_string() or
                    new_game.get_table_cards_string() != old_game.get_table_cards_string() or
                    new_game.get_positions_string() != old_game.get_positions_string()):  # Check positions too
                return True

        return False

    def clear_state(self):
        """Clear all stored state (useful for testing or reset)"""
        with self._state_lock:
            self._latest_results = {
                'timestamp': None,
                'detections': [],
                'last_update': None
            }
            self._previous_games = []