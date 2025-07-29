from typing import List, Dict, Optional, Tuple
from urllib.parse import urlencode
from loguru import logger

from src.core.domain.game import Game
from src.core.domain.street import Street
from src.core.domain.moves import MoveType
from src.core.domain.position import Position
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

            logger.info(f"FlopHeroLinkService.generate_link(game=game, full_url=full_url) {full_url}")

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
            moves = game.moves.get(street, [])
            if moves:
                # Format moves as comma-separated string
                action_strings = []
                for move_tuple in moves:
                    action_str = FlopHeroLinkService._format_single_action(move_tuple)
                    if action_str:
                        action_strings.append(action_str)

                if action_strings:
                    action_params[param_name] = ",".join(action_strings)
            else:
                action_params[param_name] = ""

        return action_params

    @staticmethod
    def _format_single_action(move_tuple: Tuple[Position, MoveType]) -> str:
        position, move_type = move_tuple
        
        # Map our action types to FlopHero format
        action_map = {
            MoveType.FOLD: 'F',
            MoveType.CALL: 'C',
            MoveType.RAISE: 'R',
            MoveType.CHECK: 'X',
            MoveType.BET: 'B',
            MoveType.ALL_IN: 'A'
        }

        return action_map.get(move_type, '')