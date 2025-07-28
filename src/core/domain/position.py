from enum import Enum
from typing import List, Set


class Position(Enum):
    """
    Poker player positions for 6-max Omaha tables.
    
    Positions are ordered by action sequence for voluntary actions
    (blinds are posted automatically and not included in action order).
    """
    
    # === 6-MAX POSITIONS ===
    EARLY_POSITION = "EP"      # Under the Gun (UTG)
    MIDDLE_POSITION = "MP"     # Middle Position
    CUTOFF = "CO"              # Cutoff 
    BUTTON = "BTN"             # Button (Dealer)
    SMALL_BLIND = "SB"         # Small Blind
    BIG_BLIND = "BB"           # Big Blind
    
    def __str__(self) -> str:
        return self.value
    
    @classmethod
    def get_action_order(cls) -> List['Position']:
        """Get positions in action order for voluntary actions (preflop and postflop)"""
        return [
            cls.EARLY_POSITION,
            cls.MIDDLE_POSITION, 
            cls.CUTOFF,
            cls.BUTTON,
            cls.SMALL_BLIND,
            cls.BIG_BLIND
        ]
    
    @classmethod
    def get_postflop_action_order(cls) -> List['Position']:
        """Get positions in postflop action order (blinds act first)"""
        return [
            cls.SMALL_BLIND,
            cls.BIG_BLIND,
            cls.EARLY_POSITION,
            cls.MIDDLE_POSITION,
            cls.CUTOFF, 
            cls.BUTTON
        ]
    
    @classmethod
    def get_blind_positions(cls) -> Set['Position']:
        """Get positions that post blinds"""
        return {cls.SMALL_BLIND, cls.BIG_BLIND}
    
    @classmethod
    def get_voluntary_positions(cls) -> Set['Position']:
        """Get positions that make voluntary actions (non-blind positions)"""
        return {
            cls.EARLY_POSITION,
            cls.MIDDLE_POSITION,
            cls.CUTOFF,
            cls.BUTTON
        }
    
    @classmethod
    def is_valid_position(cls, position: str) -> bool:
        """Check if a string represents a valid position"""
        try:
            cls(position)
            return True
        except ValueError:
            return False
    
    @classmethod
    def normalize_position(cls, position: str) -> 'Position':
        """
        Normalize common position string variations to proper Position
        
        Args:
            position: String representation of position
            
        Returns:
            Corresponding Position
            
        Raises:
            ValueError: If position cannot be normalized to a valid Position
        """
        position_upper = position.upper().strip()
        
        # Direct mapping for common variations
        position_mapping = {
            'EP': cls.EARLY_POSITION,
            'UTG': cls.EARLY_POSITION,
            'EARLY': cls.EARLY_POSITION,
            'EARLY_POSITION': cls.EARLY_POSITION,
            'MP': cls.MIDDLE_POSITION,
            'MIDDLE': cls.MIDDLE_POSITION,
            'MIDDLE_POSITION': cls.MIDDLE_POSITION,
            'CO': cls.CUTOFF,
            'CUT': cls.CUTOFF,
            'CUTOFF': cls.CUTOFF,
            'BTN': cls.BUTTON,
            'BU': cls.BUTTON,
            'BUTTON': cls.BUTTON,
            'DEALER': cls.BUTTON,
            'SB': cls.SMALL_BLIND,
            'SMALL': cls.SMALL_BLIND,
            'SMALL_BLIND': cls.SMALL_BLIND,
            'BB': cls.BIG_BLIND,
            'BIG': cls.BIG_BLIND,
            'BIG_BLIND': cls.BIG_BLIND,
        }
        
        if position_upper in position_mapping:
            return position_mapping[position_upper]
        
        # Try direct enum value lookup
        try:
            return cls(position_upper)
        except ValueError:
            raise ValueError(f"Cannot normalize position '{position}' to a valid Position")
    
    @classmethod
    def get_all_positions(cls) -> List['Position']:
        """Get all positions in clockwise order around the table"""
        return [
            cls.SMALL_BLIND,
            cls.BIG_BLIND,
            cls.EARLY_POSITION,
            cls.MIDDLE_POSITION,
            cls.CUTOFF,
            cls.BUTTON
        ]
    
    def is_blind(self) -> bool:
        """Check if this position posts a blind"""
        return self in self.get_blind_positions()
    
    def is_early_position(self) -> bool:
        """Check if this is an early position (EP/MP)"""
        return self in {self.EARLY_POSITION, self.MIDDLE_POSITION}
    
    def is_late_position(self) -> bool:
        """Check if this is a late position (CO/BTN)"""
        return self in {self.CUTOFF, self.BUTTON}


# Compatibility alias for existing code
PokerPosition = Position