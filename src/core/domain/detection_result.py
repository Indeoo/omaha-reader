from typing import List, Dict, Any, Optional
from src.core.domain.readed_card import ReadedCard
from src.core.domain.captured_image import CapturedWindow


class DetectionResult:
    """
    Represents the detection result for a single captured image.
    Replaces the result dictionary used in process_captured_images.
    """

    def __init__(
            self,
            window_name: str,
            filename: str,
            captured_image: CapturedWindow,
            player_cards: Optional[List[ReadedCard]] = None,
            table_cards: Optional[List[ReadedCard]] = None,
            positions: Optional[List[Any]] = None,
            is_player_move: bool = False
    ):
        """
        Initialize a detection result.

        Args:
            window_name: Name of the window/table
            filename: Filename of the captured image
            captured_image: CapturedImage object
            player_cards: List of detected player cards
            table_cards: List of detected table cards
            positions: List of detected positions
            is_player_move: Whether it's player's turn to move
        """
        self.window_name = window_name
        self.filename = filename
        self.captured_image = captured_image
        self.player_cards = player_cards or []
        self.table_cards = table_cards or []
        self.positions = positions or []
        self.is_player_move = is_player_move

    @property
    def has_cards(self) -> bool:
        """Check if any cards were detected"""
        return bool(self.player_cards or self.table_cards)

    @property
    def has_positions(self) -> bool:
        """Check if any positions were detected"""
        return bool(self.positions)

    @property
    def captured_item(self) -> Dict[str, Any]:
        """Backward compatibility property - returns captured_image as dict"""
        return self.captured_image.to_dict()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert back to dictionary format for backward compatibility.

        Returns:
            Dictionary representation of the detection result
        """
        return {
            'window_name': self.window_name,
            'filename': self.filename,
            'captured_item': self.captured_image.to_dict(),  # For backward compatibility
            'captured_image': self.captured_image,
            'player_cards': self.player_cards,
            'table_cards': self.table_cards,
            'positions': self.positions,
            'has_cards': self.has_cards,
            'has_positions': self.has_positions,
            'is_player_move': self.is_player_move
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DetectionResult':
        """
        Create DetectionResult from dictionary.

        Args:
            data: Dictionary containing detection result data

        Returns:
            DetectionResult instance
        """
        # Handle both old and new formats
        captured_image = data.get('captured_image')
        if captured_image is None:
            # Old format - convert from captured_item
            captured_image = CapturedWindow.from_dict(data['captured_item'])

        return cls(
            window_name=data['window_name'],
            filename=data['filename'],
            captured_image=captured_image,
            player_cards=data.get('player_cards', []),
            table_cards=data.get('table_cards', []),
            positions=data.get('positions', []),
            is_player_move=data.get('is_player_move', False)
        )

    def get_all_cards(self) -> List[ReadedCard]:
        """Get all detected cards (player + table)"""
        return self.player_cards + self.table_cards

    def __repr__(self) -> str:
        player_count = len(self.player_cards)
        table_count = len(self.table_cards)
        position_count = len(self.positions)
        move_status = "MOVE" if self.is_player_move else "WAIT"
        return (f"DetectionResult(window='{self.window_name}', "
                f"player_cards={player_count}, table_cards={table_count}, "
                f"positions={position_count}, status={move_status})")