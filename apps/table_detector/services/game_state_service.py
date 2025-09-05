from typing import List

from loguru import logger

from shared.domain.game import Game
from shared.domain.game_snapshot import GameSnapshot
from table_detector.services.state_repository import GameStateRepository


class GameStateService:

    def __init__(self, state_repository: GameStateRepository):
        self.state_repository = state_repository

    def is_new_street(self, window_name: str, detected_table_cards) -> bool:
        current_game = self.state_repository.get_by_window(window_name)

        if current_game is None:
            return True

        return current_game.table_cards != detected_table_cards

    # def is_player_move(self, detected_actions: List) -> bool:
    #     return len(detected_actions) > 0

    def create_or_update_game(self, window_name: str, game_snapshot: GameSnapshot,
                              is_new_game: bool, is_new_street: bool) -> Game:
        if is_new_game:
            current_game = self.state_repository.create_by_snapshot(window_name, game_snapshot)
            logger.info(f"Created new game for {window_name}")
        else:
            current_game = self.state_repository.get_by_window(window_name)
            if current_game is None:
                # Game doesn't exist, create it
                current_game = self.state_repository.create_by_snapshot(window_name, game_snapshot)
                logger.info(f"Created missing game for {window_name}")
            else:
                if is_new_street:
                    current_game.table_cards = game_snapshot.table_cards
                    logger.info(f"Updated table cards for {window_name} - new street")

                # Always update player cards
                current_game.player_cards = game_snapshot.player_cards

        return current_game

    def remove_windows(self, window_names: List[str]) -> bool:
        return self.state_repository.remove_windows(window_names)

