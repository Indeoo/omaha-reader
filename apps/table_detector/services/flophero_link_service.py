from typing import List, Dict, Optional, Tuple
from urllib.parse import urlencode

from loguru import logger

from shared.domain.detection import Detection
from shared.domain.game_snapshot import GameSnapshot
from shared.domain.moves import MoveType
from shared.domain.position import Position
from shared.domain.street import Street


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
    def generate_link(game: GameSnapshot) -> Optional[str]:
        try:
            params = FlopHeroLinkService.DEFAULT_PARAMS.copy()

            # Add board cards if available
            if game.table_cards:
                params['boardCards'] = FlopHeroLinkService._format_cards_for_flophero(game.table_cards)

            # Add action parameters for each street
            params.update(FlopHeroLinkService._format_actions_for_flophero(game.moves))
            params["players"] = str(len(game.get_active_position()))

            # Remove empty parameters to match REAL format
            filtered_params = {k: v for k, v in params.items() if v != ''}
            
            # Build the URL
            query_string = urlencode(filtered_params)
            full_url = f"{FlopHeroLinkService.BASE_URL}?{query_string}"

            logger.info(f"Full URL {full_url}")

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
    def _format_actions_for_flophero(moves_args) -> Dict[str, str]:
        action_params = {}

        street_param_map = {
            Street.PREFLOP: 'preflopActions',
            Street.FLOP: 'flopActions',
            Street.TURN: 'turnActions',
            Street.RIVER: 'riverActions'
        }

        for street, moves in moves_args.items():
            param_name = street_param_map.get(street)
            if param_name:
                # Format moves as comma-separated string
                action_strings = []
                for move_tuple in moves:
                    action_str = FlopHeroLinkService._format_single_action(move_tuple)
                    if action_str:
                        action_strings.append(action_str)

                action_params[param_name] = "_".join(action_strings) if action_strings else ""

        return action_params

    @staticmethod
    def _format_single_action(move_tuple: Tuple[Position, MoveType]) -> str:
        position, move_type = move_tuple
        
        # Map our action types to FlopHero format
        action_map = {
            MoveType.FOLD: 'f',
            MoveType.CALL: 'c',
            MoveType.RAISE: 'r35',
            MoveType.CHECK: 'c',
            MoveType.BET: 'b',
            MoveType.ALL_IN: 'a'
        }

        return action_map.get(move_type, '')
