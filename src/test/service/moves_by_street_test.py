import unittest
from src.core.service.moves_by_street import group_moves_by_street
from src.core.domain.moves import MoveType


class TestMovesByStreetWithExpectedResults(unittest.TestCase):
    
    def test_simple_preflop_only(self):
        """Test simple scenario where everyone folds preflop except BTN/BB"""
        input_data = {
            "EP": [MoveType.FOLD],
            "MP": [MoveType.FOLD],
            "CO": [MoveType.FOLD],
            "BTN": [MoveType.CALL],
            "SB": [MoveType.FOLD],
            "BB": [MoveType.CHECK]
        }
        
        expected_result = {
            "preflop": [MoveType.FOLD, MoveType.FOLD, MoveType.FOLD, MoveType.CALL, MoveType.FOLD, MoveType.CHECK],
            "flop": [],
            "turn": [],
            "river": []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_preflop_with_raises_complete(self):
        """Test preflop action with raises - ALL players must respond to raise"""
        input_data = {
            "EP": [MoveType.CALL, MoveType.CALL],  # call, then call the raise
            "MP": [MoveType.RAISE],         # raise
            "CO": [MoveType.FOLD],          # fold to raise
            "BTN": [MoveType.CALL],         # call the raise
            "SB": [MoveType.FOLD],          # fold to raise
            "BB": [MoveType.CALL]           # call the raise
        }
        
        expected_result = {
            "preflop": [MoveType.CALL, MoveType.RAISE, MoveType.FOLD, MoveType.CALL, MoveType.FOLD, MoveType.CALL, MoveType.CALL],
            "flop": [],
            "turn": [],
            "river": []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_multistreet_simple(self):
        """Test simple multi-street scenario"""
        input_data = {
            "EP": [MoveType.CALL, MoveType.CHECK, MoveType.FOLD],
            "MP": [MoveType.FOLD],
            "CO": [MoveType.CALL, MoveType.BET, MoveType.BET],
            "BTN": [MoveType.CALL, MoveType.CALL, MoveType.CALL],
            "SB": [MoveType.FOLD],
            "BB": [MoveType.CHECK, MoveType.CHECK, MoveType.CHECK]
        }
        
        expected_result = {
            "preflop": [MoveType.CALL, MoveType.FOLD, MoveType.CALL, MoveType.CALL, MoveType.FOLD, MoveType.CHECK],
            "flop": [MoveType.CHECK, MoveType.BET, MoveType.CALL, MoveType.CHECK],
            "turn": [MoveType.FOLD, MoveType.BET, MoveType.CALL, MoveType.CHECK],
            "river": []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_all_check_streets(self):
        """Test scenario where players check through multiple streets"""
        input_data = {
            "EP": [MoveType.CALL, MoveType.CHECK, MoveType.CHECK, MoveType.CHECK],
            "MP": [MoveType.FOLD],
            "CO": [MoveType.CALL, MoveType.CHECK, MoveType.CHECK, MoveType.CHECK],
            "BTN": [MoveType.CALL, MoveType.CHECK, MoveType.CHECK, MoveType.CHECK],
            "SB": [MoveType.FOLD],
            "BB": [MoveType.CHECK, MoveType.CHECK, MoveType.CHECK, MoveType.CHECK]
        }
        
        expected_result = {
            "preflop": [MoveType.CALL, MoveType.FOLD, MoveType.CALL, MoveType.CALL, MoveType.FOLD, MoveType.CHECK],
            "flop": [MoveType.CHECK, MoveType.CHECK, MoveType.CHECK, MoveType.CHECK],
            "turn": [MoveType.CHECK, MoveType.CHECK, MoveType.CHECK, MoveType.CHECK],
            "river": [MoveType.CHECK, MoveType.CHECK, MoveType.CHECK, MoveType.CHECK]
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_betting_round_with_aggression(self):
        """Test betting round that ends when everyone calls the aggressor"""
        input_data = {
            "EP": [MoveType.CALL, MoveType.CALL, MoveType.CHECK],  # call, call MP's raise, check flop
            "MP": [MoveType.RAISE, MoveType.BET],
            "CO": [MoveType.CALL, MoveType.CALL],
            "BTN": [MoveType.CALL, MoveType.FOLD],
            "SB": [MoveType.FOLD],
            "BB": [MoveType.CALL, MoveType.CALL]
        }
        
        expected_result = {
            "preflop": [MoveType.CALL, MoveType.RAISE, MoveType.CALL, MoveType.CALL, MoveType.FOLD, MoveType.CALL, MoveType.CALL],
            "flop": [MoveType.CHECK, MoveType.BET, MoveType.CALL, MoveType.FOLD, MoveType.CALL],
            "turn": [],
            "river": []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_single_player_scenario(self):
        """Test when only one player has actions"""
        input_data = {
            "EP": [MoveType.FOLD],
            "MP": [MoveType.FOLD],
            "CO": [MoveType.FOLD],
            "BTN": [MoveType.FOLD],
            "SB": [MoveType.FOLD],
            "BB": []
        }
        
        expected_result = {
            "preflop": [MoveType.FOLD, MoveType.FOLD, MoveType.FOLD, MoveType.FOLD, MoveType.FOLD],
            "flop": [],
            "turn": [],
            "river": []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_heads_up_scenario(self):
        """Test heads-up scenario between two players"""
        input_data = {
            "EP": [MoveType.FOLD],
            "MP": [MoveType.FOLD], 
            "CO": [MoveType.FOLD],
            "BTN": [MoveType.CALL, MoveType.BET, MoveType.CALL],
            "SB": [MoveType.FOLD],
            "BB": [MoveType.CHECK, MoveType.CALL, MoveType.CHECK]
        }
        
        expected_result = {
            "preflop": [MoveType.FOLD, MoveType.FOLD, MoveType.FOLD, MoveType.CALL, MoveType.FOLD, MoveType.CHECK],
            "flop": [MoveType.BET, MoveType.CALL],
            "turn": [MoveType.CALL, MoveType.CHECK],
            "river": []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_complex_multistreet_with_multiple_betting_rounds(self):
        """Test complex scenario with betting on multiple streets"""
        input_data = {
            "EP": [MoveType.CALL, MoveType.CHECK, MoveType.RAISE, MoveType.CALL],
            "MP": [MoveType.FOLD],
            "CO": [MoveType.RAISE, MoveType.BET, MoveType.CALL, MoveType.BET],
            "BTN": [MoveType.CALL, MoveType.CALL, MoveType.CALL, MoveType.CALL],
            "SB": [MoveType.FOLD],
            "BB": [MoveType.CALL, MoveType.CHECK, MoveType.CALL, MoveType.CALL]
        }
        
        expected_result = {
            "preflop": [MoveType.CALL, MoveType.FOLD, MoveType.RAISE, MoveType.CALL, MoveType.FOLD, MoveType.CALL],
            "flop": [MoveType.CHECK, MoveType.BET, MoveType.CALL, MoveType.CHECK],
            "turn": [MoveType.RAISE, MoveType.CALL, MoveType.CALL, MoveType.CALL],
            "river": [MoveType.CALL, MoveType.BET, MoveType.CALL, MoveType.CALL]
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_early_folds_with_continuation(self):
        """Test scenario where some players fold early but action continues"""
        input_data = {
            "EP": [MoveType.FOLD],
            "MP": [MoveType.FOLD],
            "CO": [MoveType.CALL, MoveType.CALL, MoveType.BET, MoveType.RAISE],
            "BTN": [MoveType.RAISE, MoveType.CALL, MoveType.CALL],
            "SB": [MoveType.FOLD],
            "BB": [MoveType.CALL, MoveType.CALL, MoveType.CALL]
        }
        
        expected_result = {
            "preflop": [MoveType.FOLD, MoveType.FOLD, MoveType.CALL, MoveType.RAISE, MoveType.FOLD, MoveType.CALL, MoveType.CALL],
            "flop": [MoveType.BET, MoveType.CALL, MoveType.CALL],
            "turn": [MoveType.RAISE, MoveType.CALL, MoveType.CALL],
            "river": []
        }

        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_empty_input(self):
        """Test with empty input"""
        input_data = {}
        
        expected_result = {
            "preflop": [],
            "flop": [],
            "turn": [],
            "river": []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    # ===================== OMAHA POKER RULE VALIDATION TESTS =====================

    def test_raise_requires_all_responses(self):
        """Test that ALL players who acted before a raise must respond to it"""
        input_data = {
            "EP": [MoveType.CALL, MoveType.CALL],    # calls, then must respond to CO's raise
            "MP": [MoveType.CALL, MoveType.FOLD],    # calls, then folds to CO's raise  
            "CO": [MoveType.RAISE],           # raises after EP/MP called
            "BTN": [MoveType.CALL],           # calls the raise
            "SB": [MoveType.FOLD],            # folds to raise
            "BB": [MoveType.CALL]             # calls the raise
        }
        
        expected_result = {
            "preflop": [MoveType.CALL, MoveType.CALL, MoveType.RAISE, MoveType.CALL, MoveType.FOLD, MoveType.CALL, MoveType.CALL, MoveType.FOLD],
            "flop": [],
            "turn": [],
            "river": []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_multiple_betting_rounds_same_street(self):
        """Test multiple betting rounds on the same street"""
        input_data = {
            "EP": [MoveType.CALL, MoveType.CHECK, MoveType.CALL],    # call preflop, check flop, call the raise
            "MP": [MoveType.FOLD],                     # fold preflop
            "CO": [MoveType.CALL, MoveType.BET, MoveType.RAISE],     # call preflop, bet flop, raise on flop
            "BTN": [MoveType.CALL, MoveType.CALL, MoveType.CALL],    # call preflop, call flop bet, call flop raise
            "SB": [MoveType.FOLD],                     # fold preflop
            "BB": [MoveType.CHECK, MoveType.CHECK, MoveType.CALL]    # check preflop, check flop, call flop raise
        }
        
        expected_result = {
            "preflop": [MoveType.CALL, MoveType.FOLD, MoveType.CALL, MoveType.CALL, MoveType.FOLD, MoveType.CHECK],
            "flop": [MoveType.CHECK, MoveType.BET, MoveType.CALL, MoveType.CHECK, MoveType.CALL, MoveType.RAISE, MoveType.CALL, MoveType.CALL],
            "turn": [],
            "river": []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_check_round_completion(self):
        """Test that checking rounds complete when all active players check"""
        input_data = {
            "EP": [MoveType.CALL, MoveType.CHECK],
            "MP": [MoveType.FOLD],
            "CO": [MoveType.CALL, MoveType.CHECK],
            "BTN": [MoveType.CALL, MoveType.CHECK],
            "SB": [MoveType.FOLD],
            "BB": [MoveType.CHECK, MoveType.CHECK]
        }
        
        expected_result = {
            "preflop": [MoveType.CALL, MoveType.FOLD, MoveType.CALL, MoveType.CALL, MoveType.FOLD, MoveType.CHECK],
            "flop": [MoveType.CHECK, MoveType.CHECK, MoveType.CHECK, MoveType.CHECK],
            "turn": [],
            "river": []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_bet_call_sequence(self):
        """Test proper bet-call sequence completion"""
        input_data = {
            "EP": [MoveType.CALL, MoveType.CHECK],
            "MP": [MoveType.FOLD],
            "CO": [MoveType.CALL, MoveType.BET],      # bets on flop
            "BTN": [MoveType.CALL, MoveType.CALL],    # calls flop bet
            "SB": [MoveType.FOLD],
            "BB": [MoveType.CHECK, MoveType.CALL]     # calls flop bet
        }
        
        expected_result = {
            "preflop": [MoveType.CALL, MoveType.FOLD, MoveType.CALL, MoveType.CALL, MoveType.FOLD, MoveType.CHECK],
            "flop": [MoveType.CHECK, MoveType.BET, MoveType.CALL, MoveType.CALL],
            "turn": [],
            "river": []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_three_bet_action(self):
        """Test 3-bet scenario with proper response tracking"""
        input_data = {
            "EP": [MoveType.CALL, MoveType.FOLD],         # calls, then folds to 3-bet
            "MP": [MoveType.RAISE, MoveType.FOLD],        # raises, then folds to 3-bet
            "CO": [MoveType.CALL, MoveType.RAISE],        # calls, then 3-bets 
            "BTN": [MoveType.CALL],                # calls the 3-bet
            "SB": [MoveType.FOLD],                 # folds to 3-bet
            "BB": [MoveType.CALL]                  # calls the 3-bet
        }
        
        expected_result = {
            "preflop": [MoveType.CALL, MoveType.RAISE, MoveType.CALL, MoveType.CALL, MoveType.FOLD, MoveType.CALL, MoveType.FOLD, MoveType.RAISE, MoveType.CALL, MoveType.FOLD],
            "flop": [],
            "turn": [],
            "river": []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_action_closes_when_aggressor_called(self):
        """Test that betting round closes when all players call the last aggressor"""
        input_data = {
            "EP": [MoveType.CALL, MoveType.CALL, MoveType.CHECK],  # call, call MP's raise, check flop
            "MP": [MoveType.RAISE],            # aggressor
            "CO": [MoveType.CALL],             # calls aggressor
            "BTN": [MoveType.FOLD],            # folds to aggressor
            "SB": [MoveType.FOLD],             # folds to aggressor  
            "BB": [MoveType.CALL]              # calls aggressor - round should close
        }
        
        expected_result = {
            "preflop": [MoveType.CALL, MoveType.RAISE, MoveType.CALL, MoveType.FOLD, MoveType.FOLD, MoveType.CALL, MoveType.CALL],
            "flop": [MoveType.CHECK],  # Only EP, CO, BB remain active after preflop
            "turn": [],
            "river": []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_fold_to_aggression_closes_round(self):
        """Test that betting round can close when active players fold/call aggression"""
        input_data = {
            "EP": [MoveType.CALL, MoveType.FOLD],     # calls preflop, folds to flop bet
            "MP": [MoveType.FOLD],             # foand Omaha lds preflop
            "CO": [MoveType.CALL, MoveType.BET],      # calls preflop, bets flop
            "BTN": [MoveType.CALL, MoveType.CALL],    # calls preflop, calls flop bet
            "SB": [MoveType.FOLD],             # folds preflop
            "BB": [MoveType.CHECK, MoveType.CALL]     # checks preflop, calls flop bet
        }
        
        expected_result = {
            "preflop": [MoveType.CALL, MoveType.FOLD, MoveType.CALL, MoveType.CALL, MoveType.FOLD, MoveType.CHECK],
            "flop": [MoveType.FOLD, MoveType.BET, MoveType.CALL, MoveType.CALL],
            "turn": [],
            "river": []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_position_order_enforcement(self):
        """Test that actions follow correct position order"""
        input_data = {
            "EP": [MoveType.CALL],
            "MP": [MoveType.RAISE],
            "CO": [MoveType.FOLD],
            "BTN": [MoveType.CALL],
            "SB": [MoveType.FOLD],
            "BB": [MoveType.CALL]
        }
        
        # Should be: EP, MP, CO, BTN, SB, BB order
        expected_result = {
            "preflop": [MoveType.CALL, MoveType.RAISE, MoveType.FOLD, MoveType.CALL, MoveType.FOLD, MoveType.CALL],
            "flop": [],
            "turn": [],
            "river": []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_four_street_complete_game(self):
        """Test complete 4-street game with proper betting rounds"""
        input_data = {
            "EP": [MoveType.CALL, MoveType.CHECK, MoveType.CHECK, MoveType.CHECK],
            "MP": [MoveType.FOLD],
            "CO": [MoveType.CALL, MoveType.CHECK, MoveType.CHECK, MoveType.CHECK],
            "BTN": [MoveType.CALL, MoveType.CHECK, MoveType.CHECK, MoveType.CHECK],
            "SB": [MoveType.FOLD],
            "BB": [MoveType.CHECK, MoveType.CHECK, MoveType.CHECK, MoveType.CHECK]
        }
        
        expected_result = {
            "preflop": [MoveType.CALL, MoveType.FOLD, MoveType.CALL, MoveType.CALL, MoveType.FOLD, MoveType.CHECK],
            "flop": [MoveType.CHECK, MoveType.CHECK, MoveType.CHECK, MoveType.CHECK],
            "turn": [MoveType.CHECK, MoveType.CHECK, MoveType.CHECK, MoveType.CHECK],
            "river": [MoveType.CHECK, MoveType.CHECK, MoveType.CHECK, MoveType.CHECK]
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)
