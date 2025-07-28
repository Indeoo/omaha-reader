from enum import Enum
from typing import Set


class MoveType(Enum):
    """
    Comprehensive enum for all possible move types in Omaha Poker.
    
    Includes both player actions and game state moves for complete
    poker action tracking and validation.
    """
    
    # === BASIC PLAYER ACTIONS ===
    FOLD = "fold"
    CALL = "call" 
    RAISE = "raise"
    CHECK = "check"
    BET = "bet"
    
    # # === FORCED ACTIONS ===
    # SMALL_BLIND = "sb"
    # BIG_BLIND = "bb"
    # ANTE = "ante"
    
    # === SPECIAL ACTIONS ===
    ALL_IN = "all_in"
    MUCK = "muck"
    SHOW = "show"
    
    # === TIMING ACTIONS ===
    TIME_BANK = "time_bank"
    AUTO_FOLD = "auto_fold"
    AUTO_CHECK = "auto_check"
    AUTO_CALL = "auto_call"
    
    # === GAME CONTROL ===
    SIT_OUT = "sit_out"
    SIT_IN = "sit_in"
    LEAVE_TABLE = "leave_table"
    JOIN_TABLE = "join_table"
    
    # === BETTING ROUND SPECIFIC ===
    COMPLETE = "complete"  # SB completing to full bet
    BRING_IN = "bring_in"  # Not common in Omaha but included for completeness
    
    def __str__(self) -> str:
        return self.value
    
    @classmethod
    def get_voluntary_actions(cls) -> Set['MoveType']:
        """Get all voluntary player actions (excludes forced bets and game control)"""
        return {
            cls.FOLD, cls.CALL, cls.RAISE, cls.CHECK, cls.BET,
            cls.ALL_IN, cls.MUCK, cls.SHOW, cls.COMPLETE
        }
    
    # @classmethod
    # def get_forced_actions(cls) -> Set['MoveType']:
    #     """Get all forced actions (blinds, antes)"""
    #     return {cls.SMALL_BLIND, cls.BIG_BLIND, cls.ANTE, cls.BRING_IN}
    
    @classmethod
    def get_betting_actions(cls) -> Set['MoveType']:
        """Get all actions that involve putting chips in the pot"""
        return {
            cls.CALL, cls.RAISE, cls.BET, cls.ALL_IN, cls.COMPLETE,
            cls.SMALL_BLIND, cls.BIG_BLIND, cls.ANTE, cls.BRING_IN
        }
    
    @classmethod
    def get_aggressive_actions(cls) -> Set['MoveType']:
        """Get all aggressive actions that require other players to respond"""
        return {cls.RAISE, cls.BET, cls.ALL_IN}
    
    @classmethod
    def get_passive_actions(cls) -> Set['MoveType']:
        """Get all passive actions"""
        return {cls.CALL, cls.CHECK, cls.COMPLETE}
    
    @classmethod
    def get_street_ending_actions(cls) -> Set['MoveType']:
        """Get actions that can end a betting round"""
        return {cls.FOLD, cls.CALL, cls.CHECK, cls.ALL_IN}
    
    @classmethod
    def is_valid_action(cls, action: str) -> bool:
        """Check if a string represents a valid move type"""
        try:
            cls(action)
            return True
        except ValueError:
            return False
    
    @classmethod
    def normalize_action(cls, action: str) -> 'MoveType':
        """
        Normalize common action string variations to proper MoveType
        
        Args:
            action: String representation of action
            
        Returns:
            Corresponding MoveType
            
        Raises:
            ValueError: If action cannot be normalized to a valid MoveType
        """
        action_lower = action.lower().strip()
        
        # Direct mapping
        action_mapping = {
            'fold': cls.FOLD,
            'f': cls.FOLD,
            'call': cls.CALL,
            'call_35': cls.CALL,
            'c': cls.CALL,
            'raise': cls.RAISE,
            'or_35': cls.RAISE,
            'r': cls.RAISE,
            'bet': cls.BET,
            'b': cls.BET,
            'check': cls.CHECK,
            'k': cls.CHECK,
            'x': cls.CHECK,
            # 'sb': cls.SMALL_BLIND,
            # 'small_blind': cls.SMALL_BLIND,
            # 'bb': cls.BIG_BLIND,
            # 'big_blind': cls.BIG_BLIND,
            'all_in': cls.ALL_IN,
            'allin': cls.ALL_IN,
            'all-in': cls.ALL_IN,
            'muck': cls.MUCK,
            'show': cls.SHOW,
            'complete': cls.COMPLETE,
            'comp': cls.COMPLETE,
        }
        
        if action_lower in action_mapping:
            return action_mapping[action_lower]
        
        # Try direct enum value lookup
        try:
            return cls(action_lower)
        except ValueError:
            raise ValueError(f"Cannot normalize action '{action}' to a valid MoveType")


# Compatibility alias for existing code
ActionType = MoveType