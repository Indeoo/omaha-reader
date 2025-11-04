from typing import List, Dict, Optional

from shared.domain.detection import Detection
from shared.domain.game_snapshot import GameSnapshot
from shared.utils.card_format_utils import format_cards_simple


class GameFormatService:

    @staticmethod
    def game_to_dict(window_name: str, game: GameSnapshot) -> dict:
        return {
            'window_name': window_name,
            'player_cards_string': format_cards_simple(game.player_cards),
            'table_cards_string': format_cards_simple(game.table_cards),
            'player_cards': GameFormatService._format_cards_for_web(game.player_cards),
            'table_cards': GameFormatService._format_cards_for_web(game.table_cards),
            'positions': GameFormatService._get_positions_for_web(game),
            'moves': GameFormatService._get_moves_for_web(game),
            'street': game.get_street_display(),
            'solver_link': GameFormatService._get_solver_link_for_web(game)
        }

    @staticmethod
    def _format_cards_for_web(cards: List[Detection]) -> List[Dict]:
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

    @staticmethod
    def _get_moves_for_web(game: GameSnapshot) -> List[Dict]:
        moves_by_street = []

        # Use Game's domain method to get moves by street
        for street, moves in game.moves.items():
            street_moves = []
            for position, move_type in moves:
                street_moves.append({
                    'player_label': position.name,
                    'action': move_type.value
                })

            moves_by_street.append({
                'street': street.value,
                'moves': street_moves
            })

        return moves_by_street

    @staticmethod
    def _get_solver_link_for_web(game: GameSnapshot) -> Optional[str]:
        from table_detector.services.flophero_link_service import FlopHeroLinkService

        return FlopHeroLinkService.generate_link(game)


    @staticmethod
    def _get_positions_for_web(game: GameSnapshot) -> List[Dict]:
        if not game.positions:
            return []

        formatted = []
        for player_num, position in enumerate(game.positions.values(), 1):
            formatted.append({
                'player': player_num,
                'player_label': f'Player {player_num}',
                'name': position.name,
                'is_main_player': player_num == 1
            })
        return formatted