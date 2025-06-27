#!/usr/bin/env python3
"""
Game state manager that handles game state tracking and change detection.
Updated to support all 6 player positions.
"""
import threading
from datetime import datetime
from typing import List, Optional, Tuple, Dict

from src.core.domain.detection_result import DetectionResult
from src.core.domain.game import Game
from src.core.reader.player_position_reader import PlayerPositionReader
from src.core.utils.opencv_utils import load_templates, pil_to_cv2, coords_to_search_region


class GameStateManager:
    """
    Manages game state and detects changes between detection cycles.
    Handles conversion between DetectionResult and Game objects.
    """

    # Player position coordinates on 784x584 screen
    PLAYER_POSITIONS = {
        1: {'x': 300, 'y': 375, 'w': 40, 'h': 40},  # Main player
        2: {'x': 35, 'y': 330, 'w': 40, 'h': 40},
        3: {'x': 35, 'y': 173, 'w': 40, 'h': 40},
        4: {'x': 297, 'y': 120, 'w': 40, 'h': 40},
        5: {'x': 562, 'y': 168, 'w': 40, 'h': 40},
        6: {'x': 565, 'y': 332, 'w': 40, 'h': 40}
    }

    POSITION_MARGIN = 10  # Pixels to add around each position for detection

    def __init__(self):
        # State management
        self._latest_results = {
            'timestamp': None,
            'detections': [],  # List of Game instances
            'last_update': None
        }
        self._state_lock = threading.Lock()
        self._previous_games = []

        # Initialize position readers for all players
        self._player_position_readers = {}
        self._init_all_player_position_readers()

    def _init_all_player_position_readers(self):
        """Initialize position readers for all 6 player positions"""
        try:
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
            position_templates_dir = os.path.join(project_root, "resources", "templates", "positions")

            if os.path.exists(position_templates_dir):
                position_templates = load_templates(position_templates_dir)
                if position_templates:
                    # Create a reader for each player position
                    for player_num, coords in self.PLAYER_POSITIONS.items():
                        search_region = coords_to_search_region(
                            x=coords['x'] - self.POSITION_MARGIN,
                            y=coords['y'] - self.POSITION_MARGIN,
                            w=coords['w'] + 2 * self.POSITION_MARGIN,
                            h=coords['h'] + 2 * self.POSITION_MARGIN,
                            image_width=784,
                            image_height=584
                        )

                        reader = PlayerPositionReader(position_templates)
                        reader.search_region = search_region
                        self._player_position_readers[player_num] = reader

                        print(f"✅ Player {player_num} position reader initialized with search region: {search_region}")
                else:
                    print("⚠️ No position templates found")
            else:
                print(f"⚠️ Position template directory not found: {position_templates_dir}")
        except Exception as e:
            print(f"❌ Error initializing player position readers: {str(e)}")

    def _check_all_player_positions(self, captured_image) -> Dict[int, str]:
        """
        Check all player positions in the captured image

        Args:
            captured_image: CapturedImage object to check

        Returns:
            Dictionary mapping player number to position name (e.g., {1: 'BTN', 3: 'SB', 4: 'BB'})
        """
        player_positions = {}

        if not self._player_position_readers:
            return player_positions

        try:
            # Convert PIL image to OpenCV format once
            cv2_image = pil_to_cv2(captured_image.image)

            # Check each player position
            for player_num, reader in self._player_position_readers.items():
                try:
                    detected_positions = reader.read(cv2_image)

                    if detected_positions:
                        # Take the highest confidence position
                        best_position = detected_positions[0]  # Already sorted by score
                        player_positions[player_num] = best_position.position_name

                except Exception as e:
                    print(f"❌ Error checking player {player_num} position: {str(e)}")

            return player_positions

        except Exception as e:
            print(f"❌ Error checking player positions: {str(e)}")
            return player_positions

    def update_state(self, processed_results: List[DetectionResult], timestamp_folder: str) -> bool:
        """
        Update game state with new detection results.
        Can handle both single results and batch results.

        Args:
            processed_results: List of DetectionResult objects from detection
            timestamp_folder: Timestamp folder path for tracking

        Returns:
            True if state changed and observers should be notified, False otherwise
        """
        # Convert results to games
        new_games = self._convert_results_to_games(processed_results)

        if not new_games:
            return False

        # For single game update (incremental processing)
        if len(new_games) == 1:
            new_game = new_games[0]

            # Find if this window already exists in our state
            with self._state_lock:
                existing_games = list(self._latest_results.get('detections', []))
                window_index = None
                old_game = None

                for i, game in enumerate(existing_games):
                    if game.window_name == new_game.window_name:
                        window_index = i
                        old_game = game
                        break

                # Check for changes
                has_changed = False

                if old_game is None:
                    # New window
                    has_changed = True
                    existing_games.append(new_game)
                    print(f"  🆕 New table detected: '{new_game.window_name}'")
                else:
                    # Check if game state changed
                    if (new_game.get_player_cards_string() != old_game.get_player_cards_string() or
                            new_game.get_table_cards_string() != old_game.get_table_cards_string() or
                            new_game.get_positions_string() != old_game.get_positions_string()):
                        has_changed = True
                        existing_games[window_index] = new_game

                # Perform game state checks
                if has_changed:
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

                # Check all player positions
                if processed_results[0].captured_image:
                    player_positions = self._check_all_player_positions(processed_results[0].captured_image)
                    if player_positions:
                        print(f"  👤 Player positions at '{new_game.window_name}':")
                        for player_num, position in sorted(player_positions.items()):
                            position_type = "Main player" if player_num == 1 else f"Player {player_num}"
                            print(f"     {position_type}: {position}")

                        # Store positions in the game object (you might need to add this field)
                        # new_game.player_positions = player_positions

                # Update state if changed
                if has_changed:
                    self._latest_results = {
                        'timestamp': timestamp_folder.split('/')[-1],
                        'detections': existing_games,
                        'last_update': datetime.now().isoformat()
                    }

            return has_changed

        else:
            # Batch update (original logic)
            # Check if results have changed
            has_changed = self._has_detection_changed(new_games, self._previous_games)

            # Perform game state checks for all games
            for i, (new_game, result) in enumerate(zip(new_games, processed_results)):
                # Check all player positions for each game
                if result.captured_image:
                    player_positions = self._check_all_player_positions(result.captured_image)
                    if player_positions:
                        print(f"  👤 Player positions at '{new_game.window_name}':")
                        for player_num, position in sorted(player_positions.items()):
                            position_type = "Main player" if player_num == 1 else f"Player {player_num}"
                            print(f"     {position_type}: {position}")

            if has_changed:
                with self._state_lock:
                    self._latest_results = {
                        'timestamp': timestamp_folder.split('/')[-1],
                        'detections': new_games,
                        'last_update': datetime.now().isoformat()
                    }
                self._previous_games = new_games

            return has_changed

    # ... (rest of the methods remain the same)
    def is_new_game(self, new_game: Game, old_game: Optional[Game]) -> bool:
        """Check if this is a new game based on player cards changing"""
        if old_game is None:
            return True
        return new_game.get_player_cards_string() != old_game.get_player_cards_string()

    def is_new_street(self, new_game: Game, old_game: Optional[Game]) -> bool:
        """Check if this is a new street based on table cards changing"""
        if old_game is None:
            return False
        return new_game.get_table_cards_string() != old_game.get_table_cards_string()

    def get_latest_results(self) -> dict:
        """Get the latest detection results (thread-safe)"""
        with self._state_lock:
            return {
                'timestamp': self._latest_results['timestamp'],
                'detections': [game.to_dict() for game in self._latest_results['detections']],
                'last_update': self._latest_results['last_update']
            }

    def get_notification_data(self) -> dict:
        """Get data formatted for observer notifications"""
        with self._state_lock:
            return {
                'type': 'detection_update',
                'timestamp': self._latest_results['timestamp'],
                'detections': [game.to_dict() for game in self._latest_results['detections']],
                'last_update': self._latest_results['last_update']
            }

    def _convert_results_to_games(self, processed_results: List[DetectionResult]) -> List[Game]:
        """Convert DetectionResult objects to Game instances"""
        games = []
        for result in processed_results:
            if result.has_cards or result.has_positions:
                game = Game(
                    window_name=result.window_name,
                    player_cards=result.player_cards,
                    table_cards=result.table_cards,
                    positions=result.positions
                )
                games.append(game)
        return games

    def _has_detection_changed(self, new_games: List[Game], old_games: List[Game]) -> bool:
        """Check if detection results have actually changed"""
        if len(new_games) != len(old_games):
            return True

        for new_game, old_game in zip(new_games, old_games):
            if (new_game.get_player_cards_string() != old_game.get_player_cards_string() or
                    new_game.get_table_cards_string() != old_game.get_table_cards_string() or
                    new_game.get_positions_string() != old_game.get_positions_string()):
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