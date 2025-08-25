from typing import List, Dict, Optional, Tuple
from urllib.parse import urlencode

from loguru import logger

from shared.domain.domain.detection import Detection
from shared.domain.domain.game import Game
from shared.domain.domain.moves import MoveType
from shared.domain.domain.position import Position
from shared.domain.domain.street import Street


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
    def _format_actions_for_flophero(game: Game) -> Dict[str, str]:
        action_params = {}

        # Map streets to FlopHero parameter names
        street_param_map = {
            Street.PREFLOP: 'preflopActions',
            Street.FLOP: 'flopActions',
            Street.TURN: 'turnActions',
            Street.RIVER: 'riverActions'
        }

        # Use Game's domain method to get moves by street
        for street, moves in game.get_moves_by_streets():
            param_name = street_param_map.get(street)
            if param_name:
                # Format moves as comma-separated string
                action_strings = []
                for move_tuple in moves:
                    action_str = FlopHeroLinkService._format_single_action(move_tuple)
                    if action_str:
                        action_strings.append(action_str)

                action_params[param_name] = "_".join(action_strings) if action_strings else ""

        # Ensure all expected parameters are present
        for street in game.get_street_order():
            param_name = street_param_map.get(street)
            if param_name and param_name not in action_params:
                action_params[param_name] = ""

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

#LOGGED
#https://app.flophero.com/omaha/cash/strategies?research=full_tree&site=GGPoker&bb=10&blindStructure=Regular&players=6&openRaise=3.5&stack=100&boardCards=4s4dAs&preflopActions=r35_c_f_c_c_c&flopActions=c_c_c_c_c&turnActions=c_c
#REAL
#https://app.flophero.com/omaha/cash/strategies?research=full_tree&site=GGPoker&bb=10&blindStructure=Regular&players=6&openRaise=3.5&stack=100&topRanks&suitLevel&preflopActions=r35_c_f_c_c_c&flopActions&turnActions&riverActions&boardCards=As4s4d