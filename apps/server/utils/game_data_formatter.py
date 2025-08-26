from datetime import datetime
from typing import Dict, List, Any


def format_game_data_for_web(game_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format raw game data for web display."""
    return {
        'client_id': game_data.get('client_id', ''),
        'window_name': game_data.get('window_name', ''),
        'player_cards_string': _format_cards_simple(game_data.get('player_cards', [])),
        'table_cards_string': _format_cards_simple(game_data.get('table_cards', [])),
        'player_cards': _format_cards_for_web(game_data.get('player_cards', [])),
        'table_cards': _format_cards_for_web(game_data.get('table_cards', [])),
        'positions': _format_positions_for_web(game_data.get('positions', {})),
        'moves': game_data.get('moves', []),
        'street': game_data.get('street', 'unknown'),
        'solver_link': game_data.get('solver_link'),
        'last_update': game_data.get('last_update', datetime.now().isoformat())
    }


def _format_cards_simple(cards: List[dict]) -> str:
    """Format cards as a simple string."""
    if not cards:
        return ""
    return " ".join([card.get('template_name', '') for card in cards if card.get('template_name')])


def _format_cards_for_web(cards: List[dict]) -> List[Dict]:
    """Format cards for web display with unicode symbols and match scores."""
    formatted = []
    for card in cards:
        if card.get('template_name'):
            formatted.append({
                'name': card['template_name'],
                'display': _format_card_with_unicode(card['template_name']),
                'score': round(card.get('match_score', 0), 3)
            })
    return formatted


def _format_card_with_unicode(card_name: str) -> str:
    """Format card name with unicode symbols."""
    try:
        from apps.shared.utils.card_format_utils import format_card_with_unicode
        return format_card_with_unicode(card_name)
    except ImportError:
        # Fallback if card format utils not available
        return card_name


def _format_positions_for_web(positions: Dict[str, dict]) -> List[Dict]:
    """Format position data for web display."""
    formatted = []
    for player_id_str, position_data in positions.items():
        try:
            player_num = int(player_id_str)
            formatted.append({
                'player': player_num,
                'player_label': f'Player {player_num}',
                'name': position_data.get('name', 'Unknown'),
                'is_main_player': player_num == 1
            })
        except ValueError:
            continue
    return formatted