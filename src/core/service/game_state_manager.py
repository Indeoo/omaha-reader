#!/usr/bin/env python3
"""
Game state manager that handles game state tracking and change detection.
Extracted from DetectionService for better separation of concerns.
"""
import threading
from datetime import datetime
from typing import List, Optional, Tuple

from src.core.domain.detection_result import DetectionResult
from src.core.domain.game import Game
from src.core.reader.player_position_reader import PlayerPositionReader
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

        # Initialize main player position reader
        self._main_player_position_reader = None
        self._init_main_player_position_reader()

    def _init_main_player_position_reader(self):
        """Initialize the main player position reader with templates"""
        try:
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
            position_templates_dir = os.path.join(project_root, "resources", "templates", "positions")

            if os.path.exists(position_templates_dir):
                position_templates = load_templates(position_templates_dir)
                if position_templates:
                    # Create reader with search region for main player position
                    # Main player position: 300, 375, 40, 40 on 784x584 screen
                    # Add small margin (10 pixels each side)
                    search_region = (
                        (300 - 10) / 784,  # left: ~0.369
                        (375 - 10) / 584,  # top: ~0.625
                        (300 + 40 + 10) / 784,  # right: ~0.446
                        (375 + 40 + 10) / 584  # bottom: ~0.710
                    )

                    self._main_player_position_reader = PlayerPositionReader(position_templates)
                    self._main_player_position_reader.search_region = search_region
                    print(f"✅ Main player position reader initialized with search region: {search_region}")
                else:
                    print("⚠️ No position templates found for main player")
            else:
                print(f"⚠️ Position template directory not found: {position_templates_dir}")
        except Exception as e:
            print(f"❌ Error initializing main player position reader: {str(e)}")

    def is_new_game(self, new_game: Game, old_game: Optional[Game]) -> bool:
        """
        Check if this is a new game based on player cards changing

        Args:
            new_game: Current game state
            old_game: Previous game state (can be None)

        Returns:
            True if player cards have changed (new game), False otherwise
        """
        if old_game is None:
            # First detection is always a new game
            return True

        new_player_cards = new_game.get_player_cards_string()
        old_player_cards = old_game.get_player_cards_string()

        # New game if player cards changed
        return new_player_cards != old_player_cards

    def is_new_street(self, new_game: Game, old_game: Optional[Game]) -> bool:
        """
        Check if this is a new street based on table cards changing

        Args:
            new_game: Current game state
            old_game: Previous game state (can be None)

        Returns:
            True if table cards have changed (new street), False otherwise
        """
        if old_game is None:
            # Can't determine street change without previous state
            return False

        new_table_cards = new_game.get_table_cards_string()
        old_table_cards = old_game.get_table_cards_string()

        # New street if table cards changed
        return new_table_cards != old_table_cards

    def _check_main_player_position(self, captured_image) -> Optional[str]:
        """
        Check main player position in the captured image

        Args:
            captured_image: CapturedImage object to check

        Returns:
            Position name if detected, None otherwise
        """
        if not self._main_player_position_reader:
            return None

        try:
            # Convert PIL image to OpenCV format
            cv2_image = pil_to_cv2(captured_image.image)

            # Read positions in main player area
            detected_positions = self._main_player_position_reader.read(cv2_image)

            if detected_positions:
                # Take the highest confidence position
                main_position = detected_positions[0]  # Already sorted by score
                return main_position.position_name

            return None

        except Exception as e:
            print(f"❌ Error checking main player position: {str(e)}")
            return None

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

        # Check game state changes and player positions
        for i, (new_game, result) in enumerate(zip(new_games, processed_results)):
            # Find corresponding old game
            old_game = None
            if i < len(self._previous_games):
                # Match by window name if possible
                for og in self._previous_games:
                    if og.window_name == new_game.window_name:
                        old_game = og
                        break

            # Check if new game
            if self.is_new_game(new_game, old_game):
                print(
                    f"  🆕 NEW GAME detected at '{new_game.window_name}' - Player cards: {new_game.get_player_cards_string()}")

            # Check if new street
            if self.is_new_street(new_game, old_game):
                old_street = old_game.get_street() if old_game else None
                new_street = new_game.get_street()
                print(
                    f"  🔄 NEW STREET at '{new_game.window_name}' - {old_street.value if old_street else 'Unknown'} → {new_street.value if new_street else 'Unknown'}")

            # Check main player position
            main_player_position = self._check_main_player_position(result.captured_image)
            if main_player_position:
                print(f"  👤 Main player position at '{new_game.window_name}': {main_player_position}")
            else:
                print(f"  👤 Main player position at '{new_game.window_name}': Not detected")

            # Log player move status
            if result.is_player_move:
                print(f"  ↳ Table '{new_game.window_name}' - IT'S YOUR TURN!")
            else:
                print(f"  ↳ Table '{new_game.window_name}' - Waiting for action...")

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
                # Store move status in game if needed (you might want to add this field to Game class)
                # game.is_player_move = result.is_player_move
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