from typing import List, Dict, Optional
from urllib.parse import urlencode
from loguru import logger

from src.core.domain.game import Game
from src.core.domain.street import Street
from src.core.service.move_reconstructor import ActionType
from src.core.domain.detection import Detection


class FlopHeroLinkService:
    BASE_URL = "https://app.flophero.com/omaha/cash/strategies"

    DEFAULT_PARAMS = {
        'research': 'full_tree',
        'site': 'GGPoker',
        'bb': '10',
        'blindStructure': 'Regular',
        'players': '6',
        'openRaise': '3.5',
        'stack': '100',
        'topRanks': '',
        'suitLevel': ''
    }

    @staticmethod
    def generate_link(game: Game) -> Optional[str]:
        try:
            params = FlopHeroLinkService.DEFAULT_PARAMS.copy()

            # Add board cards if available
            if game.table_cards:
                board_cards = FlopHeroLinkService._format_cards_for_flophero(game.table_cards)
                params['boardCards'] = board_cards

            # Add action parameters for each street
            params.update(FlopHeroLinkService._format_actions_for_flophero(game))
            params["players"] = str(len(game.get_active_position()))

            # Build the URL
            query_string = urlencode(params)
            full_url = f"{FlopHeroLinkService.BASE_URL}?{query_string}"

            return full_url

        except Exception as e:
            logger.error(f"Error generating FlopHero link: {str(e)}")
            return None

    @staticmethod
    def _format_cards_for_flophero(cards: List[Detection]) -> str:
        formatted = []
        for card in cards:
            if card.template_name and len(card.template_name) >= 2:
                rank = card.template_name[:-1]
                suit = card.template_name[-1].lower()
                formatted.append(f"{rank}{suit}")
        return "".join(formatted)

    @staticmethod
    def _format_actions_for_flophero(game: Game) -> Dict[str, str]:
        action_params = {}

        # Map streets to FlopHero parameter names
        street_param_map = {
            Street.PREFLOP: 'preflopActions',
            Street.FLOP: 'flopActions',
            Street.TURN: 'turnActions',
            Street.RIVER: 'riverActions'
        }

        for street, param_name in street_param_map.items():
            moves = game.get_moves_for_street(street)
            if moves:
                # Format moves as comma-separated string
                action_strings = []
                for move in moves:
                    action_str = FlopHeroLinkService._format_single_action(move)
                    if action_str:
                        action_strings.append(action_str)

                if action_strings:
                    action_params[param_name] = ",".join(action_strings)
            else:
                action_params[param_name] = ""

        return action_params

    @staticmethod
    def _format_single_action(move) -> str:
        # Map our action types to FlopHero format
        action_map = {
            ActionType.FOLD: 'F',
            ActionType.CALL: 'C',
            ActionType.RAISE: 'R',
            ActionType.CHECK: 'X',
            ActionType.SMALL_BLIND: 'SB',
            ActionType.BIG_BLIND: 'BB'
        }

        action_code = action_map.get(move.action_type, '')

        # For raises, include the amount if needed
        if move.action_type == ActionType.RAISE and move.amount > 0:
            return f"{action_code}{move.amount}"

        return action_code