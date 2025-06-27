#!/usr/bin/env python3
"""
Game state manager that handles game state tracking and change detection.
Extracted from DetectionService for better separation of concerns.
"""
import threading
from datetime import datetime
from typing import List, Dict

from src.domain.detection_result import DetectionResult
from src.domain.game import Game


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
            if result.has_cards:
                # Create game with raw ReadedCard objects
                game = Game(
                    window_name=result.window_name,
                    player_cards=result.player_cards,
                    table_cards=result.table_cards
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
                    new_game.get_table_cards_string() != old_game.get_table_cards_string()):
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