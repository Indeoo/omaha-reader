from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

from src.core.shared.message_protocol import GameUpdateMessage


@dataclass
class ClientGameState:
    client_id: str
    window_name: str
    game_data: Dict[str, Any]
    last_update: datetime
    
    def update_game_data(self, game_data: Dict[str, Any]) -> None:
        self.game_data = game_data
        self.last_update = datetime.now()

    def to_web_format(self) -> Dict[str, Any]:
        return {
            'client_id': self.client_id,
            'window_name': self.window_name,
            'player_cards_string': self._format_cards_simple(self.game_data.get('player_cards', [])),
            'table_cards_string': self._format_cards_simple(self.game_data.get('table_cards', [])),
            'player_cards': self._format_cards_for_web(self.game_data.get('player_cards', [])),
            'table_cards': self._format_cards_for_web(self.game_data.get('table_cards', [])),
            'positions': self._format_positions_for_web(self.game_data.get('positions', {})),
            'moves': self.game_data.get('moves', []),
            'street': self.game_data.get('street', 'unknown'),
            'solver_link': self.game_data.get('solver_link'),
            'last_update': self.last_update.isoformat()
        }

    def _format_cards_simple(self, cards: List[dict]) -> str:
        if not cards:
            return ""
        return " ".join([card.get('template_name', '') for card in cards if card.get('template_name')])

    def _format_cards_for_web(self, cards: List[dict]) -> List[Dict]:
        formatted = []
        for card in cards:
            if card.get('template_name'):
                formatted.append({
                    'name': card['template_name'],
                    'display': self._format_card_with_unicode(card['template_name']),
                    'score': round(card.get('match_score', 0), 3)
                })
        return formatted

    def _format_card_with_unicode(self, card_name: str) -> str:
        """Format card name with unicode symbols."""
        from src.core.utils.card_format_utils import format_card_with_unicode
        return format_card_with_unicode(card_name)

    def _format_positions_for_web(self, positions: Dict[str, dict]) -> List[Dict]:
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


class ServerGameStateService:
    def __init__(self):
        # client_id -> window_name -> ClientGameState  
        self.client_states: Dict[str, Dict[str, ClientGameState]] = {}
        self.connected_clients: Dict[str, datetime] = {}

    def register_client(self, client_id: str) -> None:
        self.connected_clients[client_id] = datetime.now()
        if client_id not in self.client_states:
            self.client_states[client_id] = {}

    def disconnect_client(self, client_id: str) -> None:
        if client_id in self.connected_clients:
            del self.connected_clients[client_id]
        if client_id in self.client_states:
            del self.client_states[client_id]

    def update_game_state(self, message: GameUpdateMessage) -> None:
        client_id = message.client_id
        window_name = message.window_name
        
        # Ensure client is registered
        if client_id not in self.client_states:
            self.client_states[client_id] = {}
        
        # Update or create game state
        if window_name in self.client_states[client_id]:
            self.client_states[client_id][window_name].update_game_data(message.game_data)
        else:
            self.client_states[client_id][window_name] = ClientGameState(
                client_id=client_id,
                window_name=window_name,
                game_data=message.game_data,
                last_update=datetime.now()
            )

    def get_all_game_states(self) -> Dict[str, Any]:
        all_detections = []
        latest_update = None
        
        for client_id, windows in self.client_states.items():
            for window_name, game_state in windows.items():
                all_detections.append(game_state.to_web_format())
                if latest_update is None or game_state.last_update > latest_update:
                    latest_update = game_state.last_update
        
        return {
            'detections': all_detections,
            'last_update': latest_update.isoformat() if latest_update else datetime.now().isoformat()
        }

    def get_client_game_states(self, client_id: str) -> List[Dict[str, Any]]:
        if client_id not in self.client_states:
            return []
        
        return [
            game_state.to_web_format() 
            for game_state in self.client_states[client_id].values()
        ]

    def get_connected_clients(self) -> List[str]:
        return list(self.connected_clients.keys())

    def remove_client_window(self, client_id: str, window_name: str) -> bool:
        if client_id in self.client_states and window_name in self.client_states[client_id]:
            del self.client_states[client_id][window_name]
            return True
        return False