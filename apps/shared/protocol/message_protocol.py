import json
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional, Any

from apps.shared.domain.detection import Detection


@dataclass
class GameUpdateMessage:
    type: str  # "game_update"
    client_id: str
    window_name: str
    timestamp: str
    game_data: Dict[str, Any]
    detection_interval: int = 3  # Default to 3 seconds matching client default

    @classmethod
    def from_dict(cls, data: dict) -> 'GameUpdateMessage':
        return cls(
            type=data['type'],
            client_id=data['client_id'],
            window_name=data['window_name'],
            timestamp=data['timestamp'],
            game_data=data['game_data'],
            detection_interval=data.get('detection_interval', 3)  # Default matching client default
        )

    def to_dict(self) -> dict:
        return {
            'type': self.type,
            'client_id': self.client_id,
            'window_name': self.window_name,
            'timestamp': self.timestamp,
            'game_data': self.game_data,
            'detection_interval': self.detection_interval
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class TableRemovalMessage:
    type: str  # "table_removal"
    client_id: str
    removed_windows: List[str]
    timestamp: str

    @classmethod
    def from_dict(cls, data: dict) -> 'TableRemovalMessage':
        return cls(
            type=data['type'],
            client_id=data['client_id'],
            removed_windows=data['removed_windows'],
            timestamp=data['timestamp']
        )

    def to_dict(self) -> dict:
        return {
            'type': self.type,
            'client_id': self.client_id,
            'removed_windows': self.removed_windows,
            'timestamp': self.timestamp
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class ServerResponseMessage:
    type: str  # "response"
    status: str  # "success" or "error"
    message: str
    timestamp: str

    def to_dict(self) -> dict:
        return {
            'type': self.type,
            'status': self.status,
            'message': self.message,
            'timestamp': self.timestamp
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class GameDataSerializer:
    @staticmethod
    def serialize_detection(detection: Detection) -> dict:
        return {
            'template_name': detection.template_name,
            'match_score': detection.match_score,
            'position': detection.position,
            'name': detection.name
        }

    @staticmethod
    def serialize_detections(detections: List[Detection]) -> List[dict]:
        return [GameDataSerializer.serialize_detection(d) for d in detections]

    @staticmethod
    def serialize_positions(positions: Dict[int, Detection]) -> Dict[str, dict]:
        return {
            str(player_id): GameDataSerializer.serialize_detection(detection)
            for player_id, detection in positions.items()
        }

    @staticmethod
    def serialize_moves(moves: List[Any]) -> List[dict]:
        # Convert moves to serializable format
        serialized_moves = []
        for move in moves:
            if hasattr(move, '__dict__'):
                serialized_moves.append(move.__dict__)
            else:
                serialized_moves.append(str(move))
        return serialized_moves


class MessageParser:
    @staticmethod
    def parse_message(message_json: str) -> Optional[Any]:
        try:
            data = json.loads(message_json)
            message_type = data.get('type')
            
            if message_type == 'game_update':
                return GameUpdateMessage.from_dict(data)
            elif message_type == 'table_removal':
                return TableRemovalMessage.from_dict(data)
            else:
                return None
        except (json.JSONDecodeError, KeyError) as e:
            return None

    @staticmethod
    def create_response(status: str, message: str) -> ServerResponseMessage:
        return ServerResponseMessage(
            type='response',
            status=status,
            message=message,
            timestamp=datetime.now().isoformat()
        )



