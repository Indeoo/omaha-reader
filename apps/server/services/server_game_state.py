from datetime import datetime
from typing import Dict, List, Any

from apps.shared.protocol.message_protocol import GameUpdateMessage


class ServerGameStateService:
    def __init__(self):
        # client_id -> window_name -> game_data_with_metadata
        self.client_states: Dict[str, Dict[str, Dict[str, Any]]] = {}
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
        
        # Update or create game state with metadata
        self.client_states[client_id][window_name] = {
            'client_id': client_id,
            'window_name': window_name,
            'last_update': datetime.now().isoformat(),
            'detection_interval': message.detection_interval,  # Include detection interval from message
            **message.game_data  # Include all game data fields
        }

    def get_all_game_states(self) -> Dict[str, Any]:
        all_detections = []
        latest_update_str = None
        
        for client_id, windows in self.client_states.items():
            for window_name, game_data in windows.items():
                all_detections.append(game_data)
                game_update = game_data.get('last_update')
                if game_update and (latest_update_str is None or game_update > latest_update_str):
                    latest_update_str = game_update
        
        return {
            'detections': all_detections,
            'last_update': latest_update_str if latest_update_str else datetime.now().isoformat()
        }

    def get_client_game_states(self, client_id: str) -> List[Dict[str, Any]]:
        if client_id not in self.client_states:
            return []
        
        return list(self.client_states[client_id].values())

    def get_connected_clients(self) -> List[str]:
        return list(self.connected_clients.keys())

    def remove_client_window(self, client_id: str, window_name: str) -> bool:
        if client_id in self.client_states and window_name in self.client_states[client_id]:
            del self.client_states[client_id][window_name]
            return True
        return False