from enum import Enum
from typing import Optional

from shared.domain.position import Position


class DetectedPosition(Enum):
    """
    Represents all possible detection values from position template matching.
    Includes both actual positions and action text that can replace position markers.
    """
    
    # ===== ACTUAL POSITIONS =====
    BUTTON = "BTN"
    SMALL_BLIND = "SB" 
    BIG_BLIND = "BB"
    EARLY_POSITION = "EP"
    MIDDLE_POSITION = "MP"
    CUTOFF = "CO"
    
    # ===== POSITION VARIATIONS =====
    BUTTON_FOLD = "BTN_fold"
    BUTTON_FOLD_RED = "BTN_fold_red"
    SMALL_BLIND_FOLD = "SB_fold"
    BIG_BLIND_FOLD = "BB_fold"
    BIG_BLIND_LOW = "BB_low"
    EARLY_POSITION_FOLD = "EP_fold"
    EARLY_POSITION_LOW = "EP_low"
    EARLY_POSITION_NOW = "EP_now"
    MIDDLE_POSITION_FOLD = "MP_fold"
    CUTOFF_FOLD = "CO_fold"
    
    # ===== ACTION TEXT (replaces position markers) =====
    FOLDS = "folds"
    CALLS = "calls"
    CALLS_1 = "calls_1"
    OPEN_RAISES = "open_raises"
    BETS = "bets"
    CHECKS = "checks"
    C_BETS = "c_bets"
    
    # ===== SPECIAL =====
    NO_POSITION = "NO"
    
    @classmethod
    def from_detection_name(cls, name: str) -> 'DetectedPosition':
        """
        Convert a detection name string to DetectedPosition enum.
        
        Args:
            name: Detection name from template matching
            
        Returns:
            DetectedPosition enum
            
        Raises:
            ValueError: If name cannot be converted to DetectedPosition
        """
        name = name.strip()
        
        # Try direct match first
        try:
            return cls(name)
        except ValueError:
            pass
            
        # Handle variations and normalize
        name_upper = name.upper()
        
        # Common variations mapping
        variations = {
            'FOLD': 'folds',
            'CALL': 'calls',
            'RAISE': 'open_raises',
            'BET': 'bets',
            'CHECK': 'checks',
            'CBET': 'c_bets',
            'C-BET': 'c_bets'
        }
        
        if name_upper in variations:
            return cls(variations[name_upper])
            
        # If still not found, raise error
        raise ValueError(f"Cannot convert '{name}' to DetectedPosition")
    
    def is_position(self) -> bool:
        """Check if this detection represents an actual poker position."""
        position_values = {
            self.BUTTON, self.SMALL_BLIND, self.BIG_BLIND,
            self.EARLY_POSITION, self.MIDDLE_POSITION, self.CUTOFF,
            # Include folded position variations as they still indicate positions
            self.BUTTON_FOLD, self.BUTTON_FOLD_RED, self.SMALL_BLIND_FOLD,
            self.BIG_BLIND_FOLD, self.BIG_BLIND_LOW, self.EARLY_POSITION_FOLD,
            self.EARLY_POSITION_LOW, self.EARLY_POSITION_NOW, self.MIDDLE_POSITION_FOLD,
            self.CUTOFF_FOLD
        }
        return self in position_values
    
    def is_action(self) -> bool:
        """Check if this detection represents action text that replaced a position marker."""
        return not self.is_position() and self != self.NO_POSITION
    
    def to_position(self) -> Optional[Position]:
        """
        Convert to actual Position enum if this represents a position.
        
        Returns:
            Position enum or None if this is not a position
        """
        if not self.is_position():
            return None
            
        # Map detected positions to actual Position enums
        # Handle both clean positions and their variations
        base_position = self._get_base_position()
        
        position_mapping = {
            "BTN": Position.BUTTON,
            "SB": Position.SMALL_BLIND,
            "BB": Position.BIG_BLIND,
            "EP": Position.EARLY_POSITION,
            "MP": Position.MIDDLE_POSITION,
            "CO": Position.CUTOFF
        }
        
        return position_mapping.get(base_position)
    
    def _get_base_position(self) -> str:
        """Extract base position name from variations like BTN_fold -> BTN."""
        value = self.value
        
        # Remove common suffixes to get base position
        suffixes = ['_fold', '_low', '_now', '_red']
        for suffix in suffixes:
            if value.endswith(suffix):
                return value[:-len(suffix)]
                
        return value
    
    def __str__(self) -> str:
        return self.value