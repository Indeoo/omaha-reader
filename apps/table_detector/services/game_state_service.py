from typing import List, Dict, Optional

from loguru import logger

from shared.domain.detection import Detection
from shared.domain.game import Game
from shared.domain.game_snapshot import GameSnapshot
from shared.domain.position import Position
from shared.utils.card_format_utils import format_cards_simple
from table_detector.services.state_repository import GameStateRepository


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
        return self.get_all_games_dict()

    def get_notification_data(self) -> dict:
        games = self.state_repository.get_all_games()
        return {
            'type': 'detection_update',
            'detections': [self._game_to_dict(window_name, game) for window_name, game in games],
            'last_update': self.state_repository.get_last_update()
        }

    def get_all_games_dict(self) -> dict:
        games = self.state_repository.get_all_games()
        return {
            'detections': [self._game_to_dict(window_name, game) for window_name, game in games],
            'last_update': self.state_repository.get_last_update()
        }

    def _game_to_dict(self, window_name: str, game: Game) -> dict:
        return {
            'window_name': window_name,
            'player_cards_string': format_cards_simple(game.player_cards),
            'table_cards_string': format_cards_simple(game.table_cards),
            'player_cards': self._format_cards_for_web(game.player_cards),
            'table_cards': self._format_cards_for_web(game.table_cards),
            'positions': self._get_positions_for_web(game),
            'moves': self._get_moves_for_web(game),
            'street': game.get_street_display(),
            'solver_link': self._get_solver_link_for_web(game)
        }

    def _format_cards_for_web(self, cards: List[Detection]) -> List[Dict]:
        if not cards:
            return []

        formatted = []
        for card in cards:
            if card.template_name:
                formatted.append({
                    'name': card.template_name,
                    'display': card.format_with_unicode(),
                    'score': round(card.match_score, 3) if card.match_score else 0
                })
        return formatted

    def _get_positions_for_web(self, game: Game) -> List[Dict]:
        if not game.positions:
            return []

        formatted = []
        for player_num, position in enumerate(game.positions.values(), 1):
            formatted.append({
                'player': player_num,
                'player_label': f'Player {player_num}',
                'name': position.position_name,
                'is_main_player': player_num == 1
            })
        return formatted

    def _get_moves_for_web(self, game: Game) -> List[Dict]:
        if not game.has_moves():
            return []

        moves_by_street = []

        # Position to player number mapping (1-indexed)
        position_to_player = {
            Position.BUTTON: 1,        # Hero position
            Position.SMALL_BLIND: 2,
            Position.BIG_BLIND: 3,
            Position.EARLY_POSITION: 4,
            Position.MIDDLE_POSITION: 5,
            Position.CUTOFF: 6
        }

        # Use Game's domain method to get moves by street
        for street, moves in game.get_moves_by_streets():
            street_moves = []
            for position, move_type in moves:
                player_number = position_to_player.get(position, 1)  # Default to player 1
                street_moves.append({
                    'player_number': player_number,
                    'player_label': f'P{player_number}',
                    'action': move_type.value,
                    'amount': 0.0,  # Not available in tuple format
                    'total_contribution': 0.0  # Not available in tuple format
                })

            moves_by_street.append({
                'street': street.value,
                'moves': street_moves
            })

        return moves_by_street


    def _get_solver_link_for_web(self, game: Game) -> Optional[str]:
        from table_detector.services.flophero_link_service import FlopHeroLinkService

        # Only generate link if we have meaningful data
        if not (game.player_cards or game.table_cards) and not game.has_moves():
            return None

        return FlopHeroLinkService.generate_link(game)