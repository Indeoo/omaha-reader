from datetime import datetime, timedelta
from typing import Dict, List, Any

from loguru import logger
from apps.shared.protocol.message_protocol import GameUpdateMessage


class ServerGameStateService:
    def __init__(self):
        # client_id -> window_name -> game_data_with_metadata
        self.client_states: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self.connected_clients: Dict[str, datetime] = {}

    def register_client(self, client_id: str) -> None:
        logger.info(f"Registering client {client_id}")
        self.connected_clients[client_id] = datetime.now()
        if client_id not in self.client_states:
            self.client_states[client_id] = {}

    def disconnect_client(self, client_id: str) -> None:
        logger.info(f"Disconnecting client {client_id}")
        if client_id in self.connected_clients:
            del self.connected_clients[client_id]
        if client_id in self.client_states:
            del self.client_states[client_id]

    def update_game_state(self, message: GameUpdateMessage) -> None:
        client_id = message.client_id
        window_name = message.window_name

        # Ensure client is registered (reuses existing registration logic)
        self.register_client(client_id)

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

    def cleanup_stale_tables(self, stale_threshold_minutes: int = 1) -> Dict[str, int]:
        """Remove tables that haven't updated recently. Remove clients with no tables left.

        Args:
            stale_threshold_minutes: Minutes of inactivity before a table is considered stale

        Returns:
            Dictionary with 'tables_removed' and 'clients_removed' counts
        """
        now = datetime.now()
        threshold = timedelta(minutes=stale_threshold_minutes)
        tables_removed = 0
        clients_to_check = []

        # Phase 1: Remove stale tables
        for client_id, windows in list(self.client_states.items()):
            for window_name, window_data in list(windows.items()):
                last_update_str = window_data.get('last_update')
                if not last_update_str:
                    # No timestamp - shouldn't happen, but skip to be safe
                    continue

                last_update = datetime.fromisoformat(last_update_str)

                if now - last_update > threshold:
                    logger.info(
                        f"🧹 Removing stale table: {client_id}/{window_name} "
                        f"(last update: {last_update.strftime('%Y-%m-%d %H:%M:%S')})"
                    )
                    self.remove_client_window(client_id, window_name)
                    tables_removed += 1

            clients_to_check.append(client_id)

        # Phase 2: Remove clients with no tables left
        clients_removed = 0
        for client_id in clients_to_check:
            if client_id in self.client_states and len(self.client_states[client_id]) == 0:
                logger.info(f"🔌 Removing client with no tables: {client_id}")
                self.disconnect_client(client_id)
                clients_removed += 1

        return {
            'tables_removed': tables_removed,
            'clients_removed': clients_removed
        }