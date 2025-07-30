from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from datetime import datetime
import json

from src.core.domain.detection import Detection


@dataclass
class GameUpdateMessage:
    type: str  # "game_update"
    client_id: str
    window_name: str
    timestamp: str
    game_data: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict) -> 'GameUpdateMessage':
        return cls(
            type=data['type'],
            client_id=data['client_id'],
            window_name=data['window_name'],
            timestamp=data['timestamp'],
            game_data=data['game_data']
        )

    def to_dict(self) -> dict:
        return {
            'type': self.type,
            'client_id': self.client_id,
            'window_name': self.window_name,
            'timestamp': self.timestamp,
            'game_data': self.game_data
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass 
class ClientRegistrationMessage:
    type: str  # "client_register"
    client_id: str
    timestamp: str

    @classmethod
    def from_dict(cls, data: dict) -> 'ClientRegistrationMessage':
        return cls(
            type=data['type'],
            client_id=data['client_id'],
            timestamp=data['timestamp']
        )

    def to_dict(self) -> dict:
        return {
            'type': self.type,
            'client_id': self.client_id,
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
            elif message_type == 'client_register':
                return ClientRegistrationMessage.from_dict(data)
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



