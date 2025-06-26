from typing import List, Dict, Any, Optional
from src.domain.readed_card import ReadedCard


class DetectionResult:
    """
    Represents the detection result for a single captured image.
    Replaces the result dictionary used in process_captured_images.
    """

    def __init__(
            self,
            index: int,
            window_name: str,
            filename: str,
            captured_item: Dict[str, Any],
            player_cards: Optional[List[ReadedCard]] = None,
            table_cards: Optional[List[ReadedCard]] = None,
            positions: Optional[List[Any]] = None
    ):
        """
        Initialize a detection result.

        Args:
            index: Index of the image in processing order
            window_name: Name of the window/table
            filename: Filename of the captured image
            captured_item: Original captured item dictionary
            player_cards: List of detected player cards
            table_cards: List of detected table cards
            positions: List of detected positions
        """
        self.index = index
        self.window_name = window_name
        self.filename = filename
        self.captured_item = captured_item
        self.player_cards = player_cards or []
        self.table_cards = table_cards or []
        self.positions = positions or []

    @property
    def has_cards(self) -> bool:
        """Check if any cards were detected"""
        return bool(self.player_cards or self.table_cards)

    @property
    def has_positions(self) -> bool:
        """Check if any positions were detected"""
        return bool(self.positions)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert back to dictionary format for backward compatibility.

        Returns:
            Dictionary representation of the detection result
        """
        return {
            'index': self.index,
            'window_name': self.window_name,
            'filename': self.filename,
            'captured_item': self.captured_item,
            'player_cards': self.player_cards,
            'table_cards': self.table_cards,
            'positions': self.positions,
            'has_cards': self.has_cards,
            'has_positions': self.has_positions
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
        return cls(
            index=data['index'],
            window_name=data['window_name'],
            filename=data['filename'],
            captured_item=data['captured_item'],
            player_cards=data.get('player_cards', []),
            table_cards=data.get('table_cards', []),
            positions=data.get('positions', [])
        )

    def get_all_cards(self) -> List[ReadedCard]:
        """Get all detected cards (player + table)"""
        return self.player_cards + self.table_cards

    def __repr__(self) -> str:
        player_count = len(self.player_cards)
        table_count = len(self.table_cards)
        position_count = len(self.positions)
        return (f"DetectionResult(window='{self.window_name}', "
                f"player_cards={player_count}, table_cards={table_count}, "
                f"positions={position_count})")