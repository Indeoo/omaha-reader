#!/usr/bin/env python3
"""
Game state manager that handles game state tracking and change detection.
"""
import threading
from datetime import datetime
from typing import List, Optional

from src.core.domain.detection_result import DetectionResult
from src.core.domain.game import Game


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

            if has_changed:
                with self._state_lock:
                    self._latest_results = {
                        'timestamp': timestamp_folder.split('/')[-1],
                        'detections': new_games,
                        'last_update': datetime.now().isoformat()
                    }
                self._previous_games = new_games

            return has_changed

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
                    positions=result.positions  # Now expecting dict
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