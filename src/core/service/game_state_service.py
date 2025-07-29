from typing import List, Dict, Optional

from loguru import logger

from src.core.domain.game import Game
from src.core.domain.game_snapshot import GameSnapshot
from src.core.domain.detection import Detection
from src.core.service.state_repository import GameStateRepository


class GameStateService:

    def __init__(self, state_repository: GameStateRepository):
        self.state_repository = state_repository

    def is_new_game(self, window_name: str, player_cards: List[Detection],
                    detected_positions: Dict[int, Detection]) -> bool:
        existing_game = self.state_repository.get_by_window(window_name)

        if existing_game is None:
            return True

        is_new_game = player_cards != existing_game.player_cards and detected_positions != existing_game.positions

        logger.info(f"{window_name} new game == {is_new_game}")

        return is_new_game

    def is_new_street(self, window_name: str, detected_table_cards) -> bool:
        current_game = self.state_repository.get_by_window(window_name)

        if current_game is None:
            return True

        return current_game.table_cards != detected_table_cards

    def is_player_move(self, detected_actions: List) -> bool:
        return len(detected_actions) > 0

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

    def get_current_game(self, window_name: str) -> Optional[Game]:
        return self.state_repository.get_by_window(window_name)

    def remove_windows(self, window_names: List[str]) -> bool:
        return self.state_repository.remove_windows(window_names)

    def get_all_games(self) -> dict:
        return self.state_repository.get_all()

    def get_notification_data(self) -> dict:
        return self.state_repository.get_notification_data()