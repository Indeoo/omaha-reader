import unittest
from src.core.service.moves_by_street import group_moves_by_street
from src.core.domain.moves import MoveType
from src.core.domain.position import Position
from src.core.domain.street import Street


class TestMovesByStreetWithExpectedResults(unittest.TestCase):
    
    def test_simple_preflop_only(self):
        """Test simple scenario where everyone folds preflop except BTN/BB"""
        input_data = {
            Position.EARLY_POSITION: [MoveType.FOLD],
            Position.MIDDLE_POSITION: [MoveType.FOLD],
            Position.CUTOFF: [MoveType.FOLD],
            Position.BUTTON: [MoveType.CALL],
            Position.SMALL_BLIND: [MoveType.FOLD],
            Position.BIG_BLIND: [MoveType.CHECK]
        }
        
        expected_result = {
            Street.PREFLOP: [
                (Position.EARLY_POSITION, MoveType.FOLD),
                (Position.MIDDLE_POSITION, MoveType.FOLD), 
                (Position.CUTOFF, MoveType.FOLD),
                (Position.BUTTON, MoveType.CALL),
                (Position.SMALL_BLIND, MoveType.FOLD),
                (Position.BIG_BLIND, MoveType.CHECK)
            ],
            Street.FLOP: [],
            Street.TURN: [],
            Street.RIVER: []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_preflop_with_raises_complete(self):
        """Test preflop action with raises - ALL players must respond to raise"""
        input_data = {
            Position.EARLY_POSITION: [MoveType.CALL, MoveType.CALL],  # call, then call the raise
            Position.MIDDLE_POSITION: [MoveType.RAISE],         # raise
            Position.CUTOFF: [MoveType.FOLD],          # fold to raise
            Position.BUTTON: [MoveType.CALL],         # call the raise
            Position.SMALL_BLIND: [MoveType.FOLD],          # fold to raise
            Position.BIG_BLIND: [MoveType.CALL]           # call the raise
        }
        
        expected_result = {
            Street.PREFLOP: [
                (Position.EARLY_POSITION, MoveType.CALL),
                (Position.MIDDLE_POSITION, MoveType.RAISE), 
                (Position.CUTOFF, MoveType.FOLD),
                (Position.BUTTON, MoveType.CALL),
                (Position.SMALL_BLIND, MoveType.FOLD),
                (Position.BIG_BLIND, MoveType.CALL),
                (Position.EARLY_POSITION, MoveType.CALL)
            ],
            Street.FLOP: [],
            Street.TURN: [],
            Street.RIVER: []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_multistreet_simple(self):
        """Test simple multi-street scenario"""
        input_data = {
            Position.EARLY_POSITION: [MoveType.CALL, MoveType.CHECK, MoveType.FOLD],
            Position.MIDDLE_POSITION: [MoveType.FOLD],
            Position.CUTOFF: [MoveType.CALL, MoveType.BET, MoveType.BET],
            Position.BUTTON: [MoveType.CALL, MoveType.CALL, MoveType.CALL],
            Position.SMALL_BLIND: [MoveType.FOLD],
            Position.BIG_BLIND: [MoveType.CHECK, MoveType.CHECK, MoveType.CHECK]
        }
        
        expected_result = {
            Street.PREFLOP: [
                (Position.EARLY_POSITION, MoveType.CALL),
                (Position.MIDDLE_POSITION, MoveType.FOLD),
                (Position.CUTOFF, MoveType.CALL),
                (Position.BUTTON, MoveType.CALL),
                (Position.SMALL_BLIND, MoveType.FOLD),
                (Position.BIG_BLIND, MoveType.CHECK)
            ],
            Street.FLOP: [
                (Position.EARLY_POSITION, MoveType.CHECK),
                (Position.CUTOFF, MoveType.BET),
                (Position.BUTTON, MoveType.CALL),
                (Position.BIG_BLIND, MoveType.CHECK)
            ],
            Street.TURN: [
                (Position.EARLY_POSITION, MoveType.FOLD),
                (Position.CUTOFF, MoveType.BET),
                (Position.BUTTON, MoveType.CALL),
                (Position.BIG_BLIND, MoveType.CHECK)
            ],
            Street.RIVER: []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_all_check_streets(self):
        """Test scenario where players check through multiple streets"""
        input_data = {
            Position.EARLY_POSITION: [MoveType.CALL, MoveType.CHECK, MoveType.CHECK, MoveType.CHECK],
            Position.MIDDLE_POSITION: [MoveType.FOLD],
            Position.CUTOFF: [MoveType.CALL, MoveType.CHECK, MoveType.CHECK, MoveType.CHECK],
            Position.BUTTON: [MoveType.CALL, MoveType.CHECK, MoveType.CHECK, MoveType.CHECK],
            Position.SMALL_BLIND: [MoveType.FOLD],
            Position.BIG_BLIND: [MoveType.CHECK, MoveType.CHECK, MoveType.CHECK, MoveType.CHECK]
        }
        
        expected_result = {
            Street.PREFLOP: [
                (Position.EARLY_POSITION, MoveType.CALL),
                (Position.MIDDLE_POSITION, MoveType.FOLD),
                (Position.CUTOFF, MoveType.CALL),
                (Position.BUTTON, MoveType.CALL),
                (Position.SMALL_BLIND, MoveType.FOLD),
                (Position.BIG_BLIND, MoveType.CHECK)
            ],
            Street.FLOP: [
                (Position.EARLY_POSITION, MoveType.CHECK),
                (Position.CUTOFF, MoveType.CHECK),
                (Position.BUTTON, MoveType.CHECK),
                (Position.BIG_BLIND, MoveType.CHECK)
            ],
            Street.TURN: [
                (Position.EARLY_POSITION, MoveType.CHECK),
                (Position.CUTOFF, MoveType.CHECK),
                (Position.BUTTON, MoveType.CHECK),
                (Position.BIG_BLIND, MoveType.CHECK)
            ],
            Street.RIVER: [
                (Position.EARLY_POSITION, MoveType.CHECK),
                (Position.CUTOFF, MoveType.CHECK),
                (Position.BUTTON, MoveType.CHECK),
                (Position.BIG_BLIND, MoveType.CHECK)
            ]
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_betting_round_with_aggression(self):
        """Test betting round that ends when everyone calls the aggressor"""
        input_data = {
            Position.EARLY_POSITION: [MoveType.CALL, MoveType.CALL, MoveType.CHECK],  # call, call MP's raise, check flop
            Position.MIDDLE_POSITION: [MoveType.RAISE, MoveType.BET],
            Position.CUTOFF: [MoveType.CALL, MoveType.CALL],
            Position.BUTTON: [MoveType.CALL, MoveType.FOLD],
            Position.SMALL_BLIND: [MoveType.FOLD],
            Position.BIG_BLIND: [MoveType.CALL, MoveType.CALL]
        }
        
        expected_result = {
            Street.PREFLOP: [
                (Position.EARLY_POSITION, MoveType.CALL),
                (Position.MIDDLE_POSITION, MoveType.RAISE),
                (Position.CUTOFF, MoveType.CALL),
                (Position.BUTTON, MoveType.CALL),
                (Position.SMALL_BLIND, MoveType.FOLD),
                (Position.BIG_BLIND, MoveType.CALL),
                (Position.EARLY_POSITION, MoveType.CALL)
            ],
            Street.FLOP: [
                (Position.EARLY_POSITION, MoveType.CHECK),
                (Position.MIDDLE_POSITION, MoveType.BET),
                (Position.CUTOFF, MoveType.CALL),
                (Position.BUTTON, MoveType.FOLD),
                (Position.BIG_BLIND, MoveType.CALL)
            ],
            Street.TURN: [],
            Street.RIVER: []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_single_player_scenario(self):
        """Test when only one player has actions"""
        input_data = {
            Position.EARLY_POSITION: [MoveType.FOLD],
            Position.MIDDLE_POSITION: [MoveType.FOLD],
            Position.CUTOFF: [MoveType.FOLD],
            Position.BUTTON: [MoveType.FOLD],
            Position.SMALL_BLIND: [MoveType.FOLD],
            Position.BIG_BLIND: []
        }
        
        expected_result = {
            Street.PREFLOP: [
                (Position.EARLY_POSITION, MoveType.FOLD),
                (Position.MIDDLE_POSITION, MoveType.FOLD),
                (Position.CUTOFF, MoveType.FOLD),
                (Position.BUTTON, MoveType.FOLD),
                (Position.SMALL_BLIND, MoveType.FOLD)
            ],
            Street.FLOP: [],
            Street.TURN: [],
            Street.RIVER: []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_heads_up_scenario(self):
        """Test heads-up scenario between two players"""
        input_data = {
            Position.EARLY_POSITION: [MoveType.FOLD],
            Position.MIDDLE_POSITION: [MoveType.FOLD], 
            Position.CUTOFF: [MoveType.FOLD],
            Position.BUTTON: [MoveType.CALL, MoveType.BET, MoveType.CALL],
            Position.SMALL_BLIND: [MoveType.FOLD],
            Position.BIG_BLIND: [MoveType.CHECK, MoveType.CALL, MoveType.CHECK]
        }
        
        expected_result = {
            Street.PREFLOP: [
                (Position.EARLY_POSITION, MoveType.FOLD),
                (Position.MIDDLE_POSITION, MoveType.FOLD),
                (Position.CUTOFF, MoveType.FOLD),
                (Position.BUTTON, MoveType.CALL),
                (Position.SMALL_BLIND, MoveType.FOLD),
                (Position.BIG_BLIND, MoveType.CHECK)
            ],
            Street.FLOP: [
                (Position.BUTTON, MoveType.BET),
                (Position.BIG_BLIND, MoveType.CALL)
            ],
            Street.TURN: [
                (Position.BUTTON, MoveType.CALL),
                (Position.BIG_BLIND, MoveType.CHECK)
            ],
            Street.RIVER: []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_complex_multistreet_with_multiple_betting_rounds(self):
        """Test complex scenario with betting on multiple streets"""
        input_data = {
            Position.EARLY_POSITION: [MoveType.CALL, MoveType.CHECK, MoveType.RAISE, MoveType.CALL],
            Position.MIDDLE_POSITION: [MoveType.FOLD],
            Position.CUTOFF: [MoveType.RAISE, MoveType.BET, MoveType.CALL, MoveType.BET],
            Position.BUTTON: [MoveType.CALL, MoveType.CALL, MoveType.CALL, MoveType.CALL],
            Position.SMALL_BLIND: [MoveType.FOLD],
            Position.BIG_BLIND: [MoveType.CALL, MoveType.CHECK, MoveType.CALL, MoveType.CALL]
        }
        
        expected_result = {
            Street.PREFLOP: [
                (Position.EARLY_POSITION, MoveType.CALL),
                (Position.MIDDLE_POSITION, MoveType.FOLD),
                (Position.CUTOFF, MoveType.RAISE),
                (Position.BUTTON, MoveType.CALL),
                (Position.SMALL_BLIND, MoveType.FOLD),
                (Position.BIG_BLIND, MoveType.CALL)
            ],
            Street.FLOP: [
                (Position.EARLY_POSITION, MoveType.CHECK),
                (Position.CUTOFF, MoveType.BET),
                (Position.BUTTON, MoveType.CALL),
                (Position.BIG_BLIND, MoveType.CHECK)
            ],
            Street.TURN: [
                (Position.EARLY_POSITION, MoveType.RAISE),
                (Position.CUTOFF, MoveType.CALL),
                (Position.BUTTON, MoveType.CALL),
                (Position.BIG_BLIND, MoveType.CALL)
            ],
            Street.RIVER: [
                (Position.EARLY_POSITION, MoveType.CALL),
                (Position.CUTOFF, MoveType.BET),
                (Position.BUTTON, MoveType.CALL),
                (Position.BIG_BLIND, MoveType.CALL)
            ]
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_early_folds_with_continuation(self):
        """Test scenario where some players fold early but action continues"""
        input_data = {
            Position.EARLY_POSITION: [MoveType.FOLD],
            Position.MIDDLE_POSITION: [MoveType.FOLD],
            Position.CUTOFF: [MoveType.CALL, MoveType.CALL, MoveType.BET, MoveType.RAISE],
            Position.BUTTON: [MoveType.RAISE, MoveType.CALL, MoveType.CALL],
            Position.SMALL_BLIND: [MoveType.FOLD],
            Position.BIG_BLIND: [MoveType.CALL, MoveType.CALL, MoveType.CALL]
        }
        
        expected_result = {
            Street.PREFLOP: [
                (Position.EARLY_POSITION, MoveType.FOLD),
                (Position.MIDDLE_POSITION, MoveType.FOLD),
                (Position.CUTOFF, MoveType.CALL),
                (Position.BUTTON, MoveType.RAISE),
                (Position.SMALL_BLIND, MoveType.FOLD),
                (Position.BIG_BLIND, MoveType.CALL),
                (Position.CUTOFF, MoveType.CALL)
            ],
            Street.FLOP: [
                (Position.CUTOFF, MoveType.BET),
                (Position.BUTTON, MoveType.CALL),
                (Position.BIG_BLIND, MoveType.CALL)
            ],
            Street.TURN: [
                (Position.CUTOFF, MoveType.RAISE),
                (Position.BUTTON, MoveType.CALL),
                (Position.BIG_BLIND, MoveType.CALL)
            ],
            Street.RIVER: []
        }

        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_empty_input(self):
        """Test with empty input"""
        input_data = {}
        
        expected_result = {
            Street.PREFLOP: [],
            Street.FLOP: [],
            Street.TURN: [],
            Street.RIVER: []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    # ===================== OMAHA POKER RULE VALIDATION TESTS =====================

    def test_raise_requires_all_responses(self):
        """Test that ALL players who acted before a raise must respond to it"""
        input_data = {
            Position.EARLY_POSITION: [MoveType.CALL, MoveType.CALL],    # calls, then must respond to CO's raise
            Position.MIDDLE_POSITION: [MoveType.CALL, MoveType.FOLD],    # calls, then folds to CO's raise  
            Position.CUTOFF: [MoveType.RAISE],           # raises after EP/MP called
            Position.BUTTON: [MoveType.CALL],           # calls the raise
            Position.SMALL_BLIND: [MoveType.FOLD],            # folds to raise
            Position.BIG_BLIND: [MoveType.CALL]             # calls the raise
        }
        
        expected_result = {
            Street.PREFLOP: [
                (Position.EARLY_POSITION, MoveType.CALL),
                (Position.MIDDLE_POSITION, MoveType.CALL),
                (Position.CUTOFF, MoveType.RAISE),
                (Position.BUTTON, MoveType.CALL),
                (Position.SMALL_BLIND, MoveType.FOLD),
                (Position.BIG_BLIND, MoveType.CALL),
                (Position.EARLY_POSITION, MoveType.CALL),
                (Position.MIDDLE_POSITION, MoveType.FOLD)
            ],
            Street.FLOP: [],
            Street.TURN: [],
            Street.RIVER: []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_multiple_betting_rounds_same_street(self):
        """Test multiple betting rounds on the same street"""
        input_data = {
            Position.EARLY_POSITION: [MoveType.CALL, MoveType.CHECK, MoveType.CALL],    # call preflop, check flop, call the raise
            Position.MIDDLE_POSITION: [MoveType.FOLD],                     # fold preflop
            Position.CUTOFF: [MoveType.CALL, MoveType.BET, MoveType.RAISE],     # call preflop, bet flop, raise on flop
            Position.BUTTON: [MoveType.CALL, MoveType.CALL, MoveType.CALL],    # call preflop, call flop bet, call flop raise
            Position.SMALL_BLIND: [MoveType.FOLD],                     # fold preflop
            Position.BIG_BLIND: [MoveType.CHECK, MoveType.CHECK, MoveType.CALL]    # check preflop, check flop, call flop raise
        }
        
        expected_result = {
            Street.PREFLOP: [
                (Position.EARLY_POSITION, MoveType.CALL),
                (Position.MIDDLE_POSITION, MoveType.FOLD),
                (Position.CUTOFF, MoveType.CALL),
                (Position.BUTTON, MoveType.CALL),
                (Position.SMALL_BLIND, MoveType.FOLD),
                (Position.BIG_BLIND, MoveType.CHECK)
            ],
            Street.FLOP: [
                (Position.EARLY_POSITION, MoveType.CHECK),
                (Position.CUTOFF, MoveType.BET),
                (Position.BUTTON, MoveType.CALL),
                (Position.BIG_BLIND, MoveType.CHECK),
                (Position.EARLY_POSITION, MoveType.CALL),
                (Position.CUTOFF, MoveType.RAISE),
                (Position.BUTTON, MoveType.CALL),
                (Position.BIG_BLIND, MoveType.CALL)
            ],
            Street.TURN: [],
            Street.RIVER: []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_check_round_completion(self):
        """Test that checking rounds complete when all active players check"""
        input_data = {
            Position.EARLY_POSITION: [MoveType.CALL, MoveType.CHECK],
            Position.MIDDLE_POSITION: [MoveType.FOLD],
            Position.CUTOFF: [MoveType.CALL, MoveType.CHECK],
            Position.BUTTON: [MoveType.CALL, MoveType.CHECK],
            Position.SMALL_BLIND: [MoveType.FOLD],
            Position.BIG_BLIND: [MoveType.CHECK, MoveType.CHECK]
        }
        
        expected_result = {
            Street.PREFLOP: [
                (Position.EARLY_POSITION, MoveType.CALL),
                (Position.MIDDLE_POSITION, MoveType.FOLD),
                (Position.CUTOFF, MoveType.CALL),
                (Position.BUTTON, MoveType.CALL),
                (Position.SMALL_BLIND, MoveType.FOLD),
                (Position.BIG_BLIND, MoveType.CHECK)
            ],
            Street.FLOP: [
                (Position.EARLY_POSITION, MoveType.CHECK),
                (Position.CUTOFF, MoveType.CHECK),
                (Position.BUTTON, MoveType.CHECK),
                (Position.BIG_BLIND, MoveType.CHECK)
            ],
            Street.TURN: [],
            Street.RIVER: []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_bet_call_sequence(self):
        """Test proper bet-call sequence completion"""
        input_data = {
            Position.EARLY_POSITION: [MoveType.CALL, MoveType.CHECK],
            Position.MIDDLE_POSITION: [MoveType.FOLD],
            Position.CUTOFF: [MoveType.CALL, MoveType.BET],      # bets on flop
            Position.BUTTON: [MoveType.CALL, MoveType.CALL],    # calls flop bet
            Position.SMALL_BLIND: [MoveType.FOLD],
            Position.BIG_BLIND: [MoveType.CHECK, MoveType.CALL]     # calls flop bet
        }
        
        expected_result = {
            Street.PREFLOP: [
                (Position.EARLY_POSITION, MoveType.CALL),
                (Position.MIDDLE_POSITION, MoveType.FOLD),
                (Position.CUTOFF, MoveType.CALL),
                (Position.BUTTON, MoveType.CALL),
                (Position.SMALL_BLIND, MoveType.FOLD),
                (Position.BIG_BLIND, MoveType.CHECK)
            ],
            Street.FLOP: [
                (Position.EARLY_POSITION, MoveType.CHECK),
                (Position.CUTOFF, MoveType.BET),
                (Position.BUTTON, MoveType.CALL),
                (Position.BIG_BLIND, MoveType.CALL)
            ],
            Street.TURN: [],
            Street.RIVER: []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_three_bet_action(self):
        """Test 3-bet scenario with proper response tracking"""
        input_data = {
            Position.EARLY_POSITION: [MoveType.CALL, MoveType.FOLD],         # calls, then folds to 3-bet
            Position.MIDDLE_POSITION: [MoveType.RAISE, MoveType.FOLD],        # raises, then folds to 3-bet
            Position.CUTOFF: [MoveType.CALL, MoveType.RAISE],        # calls, then 3-bets 
            Position.BUTTON: [MoveType.CALL],                # calls the 3-bet
            Position.SMALL_BLIND: [MoveType.FOLD],                 # folds to 3-bet
            Position.BIG_BLIND: [MoveType.CALL]                  # calls the 3-bet
        }
        
        expected_result = {
            Street.PREFLOP: [
                (Position.EARLY_POSITION, MoveType.CALL),
                (Position.MIDDLE_POSITION, MoveType.RAISE),
                (Position.CUTOFF, MoveType.CALL),
                (Position.BUTTON, MoveType.CALL),
                (Position.SMALL_BLIND, MoveType.FOLD),
                (Position.BIG_BLIND, MoveType.CALL),
                (Position.EARLY_POSITION, MoveType.FOLD),
                (Position.MIDDLE_POSITION, MoveType.FOLD),
                (Position.CUTOFF, MoveType.RAISE),
                (Position.BUTTON, MoveType.CALL),
                (Position.BIG_BLIND, MoveType.FOLD)
            ],
            Street.FLOP: [],
            Street.TURN: [],
            Street.RIVER: []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_action_closes_when_aggressor_called(self):
        """Test that betting round closes when all players call the last aggressor"""
        input_data = {
            Position.EARLY_POSITION: [MoveType.CALL, MoveType.CALL, MoveType.CHECK],  # call, call MP's raise, check flop
            Position.MIDDLE_POSITION: [MoveType.RAISE],            # aggressor
            Position.CUTOFF: [MoveType.CALL],             # calls aggressor
            Position.BUTTON: [MoveType.FOLD],            # folds to aggressor
            Position.SMALL_BLIND: [MoveType.FOLD],             # folds to aggressor  
            Position.BIG_BLIND: [MoveType.CALL]              # calls aggressor - round should close
        }
        
        expected_result = {
            Street.PREFLOP: [
                (Position.EARLY_POSITION, MoveType.CALL),
                (Position.MIDDLE_POSITION, MoveType.RAISE),
                (Position.CUTOFF, MoveType.CALL),
                (Position.BUTTON, MoveType.FOLD),
                (Position.SMALL_BLIND, MoveType.FOLD),
                (Position.BIG_BLIND, MoveType.CALL),
                (Position.EARLY_POSITION, MoveType.CALL)
            ],
            Street.FLOP: [
                (Position.EARLY_POSITION, MoveType.CHECK)
            ],
            Street.TURN: [],
            Street.RIVER: []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_fold_to_aggression_closes_round(self):
        """Test that betting round can close when active players fold/call aggression"""
        input_data = {
            Position.EARLY_POSITION: [MoveType.CALL, MoveType.FOLD],     # calls preflop, folds to flop bet
            Position.MIDDLE_POSITION: [MoveType.FOLD],             # foand Omaha lds preflop
            Position.CUTOFF: [MoveType.CALL, MoveType.BET],      # calls preflop, bets flop
            Position.BUTTON: [MoveType.CALL, MoveType.CALL],    # calls preflop, calls flop bet
            Position.SMALL_BLIND: [MoveType.FOLD],             # folds preflop
            Position.BIG_BLIND: [MoveType.CHECK, MoveType.CALL]     # checks preflop, calls flop bet
        }
        
        expected_result = {
            Street.PREFLOP: [
                (Position.EARLY_POSITION, MoveType.CALL),
                (Position.MIDDLE_POSITION, MoveType.FOLD),
                (Position.CUTOFF, MoveType.CALL),
                (Position.BUTTON, MoveType.CALL),
                (Position.SMALL_BLIND, MoveType.FOLD),
                (Position.BIG_BLIND, MoveType.CHECK)
            ],
            Street.FLOP: [
                (Position.EARLY_POSITION, MoveType.FOLD),
                (Position.CUTOFF, MoveType.BET),
                (Position.BUTTON, MoveType.CALL),
                (Position.BIG_BLIND, MoveType.CALL)
            ],
            Street.TURN: [],
            Street.RIVER: []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_position_order_enforcement(self):
        """Test that actions follow correct position order"""
        input_data = {
            Position.EARLY_POSITION: [MoveType.CALL],
            Position.MIDDLE_POSITION: [MoveType.RAISE],
            Position.CUTOFF: [MoveType.FOLD],
            Position.BUTTON: [MoveType.CALL],
            Position.SMALL_BLIND: [MoveType.FOLD],
            Position.BIG_BLIND: [MoveType.CALL]
        }
        
        # Should be: EP, MP, CO, BTN, SB, BB order
        expected_result = {
            Street.PREFLOP: [
                (Position.EARLY_POSITION, MoveType.CALL),
                (Position.MIDDLE_POSITION, MoveType.RAISE),
                (Position.CUTOFF, MoveType.FOLD),
                (Position.BUTTON, MoveType.CALL),
                (Position.SMALL_BLIND, MoveType.FOLD),
                (Position.BIG_BLIND, MoveType.CALL)
            ],
            Street.FLOP: [],
            Street.TURN: [],
            Street.RIVER: []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_four_street_complete_game(self):
        """Test complete 4-street game with proper betting rounds"""
        input_data = {
            Position.EARLY_POSITION: [MoveType.CALL, MoveType.CHECK, MoveType.CHECK, MoveType.CHECK],
            Position.MIDDLE_POSITION: [MoveType.FOLD],
            Position.CUTOFF: [MoveType.CALL, MoveType.CHECK, MoveType.CHECK, MoveType.CHECK],
            Position.BUTTON: [MoveType.CALL, MoveType.CHECK, MoveType.CHECK, MoveType.CHECK],
            Position.SMALL_BLIND: [MoveType.FOLD],
            Position.BIG_BLIND: [MoveType.CHECK, MoveType.CHECK, MoveType.CHECK, MoveType.CHECK]
        }
        
        expected_result = {
            Street.PREFLOP: [
                (Position.EARLY_POSITION, MoveType.CALL),
                (Position.MIDDLE_POSITION, MoveType.FOLD),
                (Position.CUTOFF, MoveType.CALL),
                (Position.BUTTON, MoveType.CALL),
                (Position.SMALL_BLIND, MoveType.FOLD),
                (Position.BIG_BLIND, MoveType.CHECK)
            ],
            Street.FLOP: [
                (Position.EARLY_POSITION, MoveType.CHECK),
                (Position.CUTOFF, MoveType.CHECK),
                (Position.BUTTON, MoveType.CHECK),
                (Position.BIG_BLIND, MoveType.CHECK)
            ],
            Street.TURN: [
                (Position.EARLY_POSITION, MoveType.CHECK),
                (Position.CUTOFF, MoveType.CHECK),
                (Position.BUTTON, MoveType.CHECK),
                (Position.BIG_BLIND, MoveType.CHECK)
            ],
            Street.RIVER: [
                (Position.EARLY_POSITION, MoveType.CHECK),
                (Position.CUTOFF, MoveType.CHECK),
                (Position.BUTTON, MoveType.CHECK),
                (Position.BIG_BLIND, MoveType.CHECK)
            ]
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)
