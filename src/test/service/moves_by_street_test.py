import unittest
from src.core.service.moves_by_street import group_moves_by_street


class TestMovesByStreetWithExpectedResults(unittest.TestCase):
    
    def test_simple_preflop_only(self):
        """Test simple scenario where everyone folds preflop except BTN/BB"""
        input_data = {
            "EP": ["fold"],
            "MP": ["fold"],
            "CO": ["fold"],
            "BTN": ["call"],
            "SB": ["fold"],
            "BB": ["check"]
        }
        
        expected_result = {
            "preflop": ["fold", "fold", "fold", "call", "fold", "check"],
            "flop": [],
            "turn": [],
            "river": []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_preflop_with_raises_complete(self):
        """Test preflop action with raises - ALL players must respond to raise"""
        input_data = {
            "EP": ["call", "call"],  # call, then call the raise
            "MP": ["raise"],         # raise
            "CO": ["fold"],          # fold to raise
            "BTN": ["call"],         # call the raise
            "SB": ["fold"],          # fold to raise
            "BB": ["call"]           # call the raise
        }
        
        expected_result = {
            "preflop": ["call", "raise", "fold", "call", "fold", "call", "call"],
            "flop": [],
            "turn": [],
            "river": []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_multistreet_simple(self):
        """Test simple multi-street scenario"""
        input_data = {
            "EP": ["call", "check", "fold"],
            "MP": ["fold"],
            "CO": ["call", "bet", "bet"],
            "BTN": ["call", "call", "call"],
            "SB": ["fold"],
            "BB": ["check", "check", "check"]
        }
        
        expected_result = {
            "preflop": ["call", "fold", "call", "call", "fold", "check"],
            "flop": ["check", "bet", "call", "check"],
            "turn": ["fold", "bet", "call", "check"],
            "river": []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_all_check_streets(self):
        """Test scenario where players check through multiple streets"""
        input_data = {
            "EP": ["call", "check", "check", "check"],
            "MP": ["fold"],
            "CO": ["call", "check", "check", "check"],
            "BTN": ["call", "check", "check", "check"],
            "SB": ["fold"],
            "BB": ["check", "check", "check", "check"]
        }
        
        expected_result = {
            "preflop": ["call", "fold", "call", "call", "fold", "check"],
            "flop": ["check", "check", "check", "check"],
            "turn": ["check", "check", "check", "check"],
            "river": ["check", "check", "check", "check"]
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_betting_round_with_aggression(self):
        """Test betting round that ends when everyone calls the aggressor"""
        input_data = {
            "EP": ["call", "check"],
            "MP": ["raise", "bet"],
            "CO": ["call", "call"],
            "BTN": ["call", "fold"],
            "SB": ["fold"],
            "BB": ["call", "call"]
        }
        
        expected_result = {
            "preflop": ["call", "raise", "call", "call", "fold", "call"],
            "flop": ["check", "bet", "call", "fold", "call"],
            "turn": [],
            "river": []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_single_player_scenario(self):
        """Test when only one player has actions"""
        input_data = {
            "EP": ["fold"],
            "MP": ["fold"],
            "CO": ["fold"],
            "BTN": ["fold"],
            "SB": ["fold"],
            "BB": []
        }
        
        expected_result = {
            "preflop": ["fold", "fold", "fold", "fold", "fold"],
            "flop": [],
            "turn": [],
            "river": []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_heads_up_scenario(self):
        """Test heads-up scenario between two players"""
        input_data = {
            "EP": ["fold"],
            "MP": ["fold"], 
            "CO": ["fold"],
            "BTN": ["call", "bet", "call"],
            "SB": ["fold"],
            "BB": ["check", "call", "check"]
        }
        
        expected_result = {
            "preflop": ["fold", "fold", "fold", "call", "fold", "check"],
            "flop": ["bet", "call"],
            "turn": ["call", "check"],
            "river": []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_complex_multistreet_with_multiple_betting_rounds(self):
        """Test complex scenario with betting on multiple streets"""
        input_data = {
            "EP": ["call", "check", "raise", "call"],
            "MP": ["fold"],
            "CO": ["raise", "bet", "call", "bet"],
            "BTN": ["call", "call", "call", "call"],
            "SB": ["fold"],
            "BB": ["call", "check", "call", "call"]
        }
        
        expected_result = {
            "preflop": ["call", "fold", "raise", "call", "fold", "call"],
            "flop": ["check", "bet", "call", "check"],
            "turn": ["raise", "call", "call", "call"],
            "river": ["call", "bet", "call", "call"]
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_early_folds_with_continuation(self):
        """Test scenario where some players fold early but action continues"""
        input_data = {
            "EP": ["fold"],
            "MP": ["fold"],
            "CO": ["call", "call", "bet", "raise"],
            "BTN": ["raise", "call", "call"],
            "SB": ["fold"],
            "BB": ["call", "call", "call"]
        }
        
        expected_result = {
            "preflop": ["fold", "fold", "call", "raise", "fold", "call", "call"],
            "flop": ["bet", "call", "call"],
            "turn": ["raise", "call", "call"],
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
            "EP": ["call", "call"],    # calls, then must respond to CO's raise
            "MP": ["call", "fold"],    # calls, then folds to CO's raise  
            "CO": ["raise"],           # raises after EP/MP called
            "BTN": ["call"],           # calls the raise
            "SB": ["fold"],            # folds to raise
            "BB": ["call"]             # calls the raise
        }
        
        expected_result = {
            "preflop": ["call", "call", "raise", "call", "fold", "call", "call", "fold"],
            "flop": [],
            "turn": [],
            "river": []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_multiple_betting_rounds_same_street(self):
        """Test multiple betting rounds on the same street"""
        input_data = {
            "EP": ["call", "check", "call"],    # call preflop, check flop, call the raise
            "MP": ["fold"],                     # fold preflop
            "CO": ["call", "bet", "raise"],     # call preflop, bet flop, raise on flop
            "BTN": ["call", "call", "call"],    # call preflop, call flop bet, call flop raise
            "SB": ["fold"],                     # fold preflop
            "BB": ["check", "check", "call"]    # check preflop, check flop, call flop raise
        }
        
        expected_result = {
            "preflop": ["call", "fold", "call", "call", "fold", "check"],
            "flop": ["check", "bet", "call", "check", "call", "raise", "call", "call"],
            "turn": [],
            "river": []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_check_round_completion(self):
        """Test that checking rounds complete when all active players check"""
        input_data = {
            "EP": ["call", "check"],
            "MP": ["fold"],
            "CO": ["call", "check"],
            "BTN": ["call", "check"],
            "SB": ["fold"],
            "BB": ["check", "check"]
        }
        
        expected_result = {
            "preflop": ["call", "fold", "call", "call", "fold", "check"],
            "flop": ["check", "check", "check", "check"],
            "turn": [],
            "river": []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_bet_call_sequence(self):
        """Test proper bet-call sequence completion"""
        input_data = {
            "EP": ["call", "check"],
            "MP": ["fold"],
            "CO": ["call", "bet"],      # bets on flop
            "BTN": ["call", "call"],    # calls flop bet
            "SB": ["fold"],
            "BB": ["check", "call"]     # calls flop bet
        }
        
        expected_result = {
            "preflop": ["call", "fold", "call", "call", "fold", "check"],
            "flop": ["check", "bet", "call", "call"],
            "turn": [],
            "river": []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_three_bet_action(self):
        """Test 3-bet scenario with proper response tracking"""
        input_data = {
            "EP": ["call", "fold"],         # calls, then folds to 3-bet
            "MP": ["raise", "fold"],        # raises, then folds to 3-bet
            "CO": ["call", "raise"],        # calls, then 3-bets 
            "BTN": ["call"],                # calls the 3-bet
            "SB": ["fold"],                 # folds to 3-bet
            "BB": ["call"]                  # calls the 3-bet
        }
        
        expected_result = {
            "preflop": ["call", "raise", "call", "call", "fold", "call", "fold", "raise", "call", "fold"],
            "flop": [],
            "turn": [],
            "river": []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_action_closes_when_aggressor_called(self):
        """Test that betting round closes when all players call the last aggressor"""
        input_data = {
            "EP": ["call", "check"],
            "MP": ["raise"],            # aggressor
            "CO": ["call"],             # calls aggressor
            "BTN": ["fold"],            # folds to aggressor
            "SB": ["fold"],             # folds to aggressor  
            "BB": ["call"]              # calls aggressor - round should close
        }
        
        expected_result = {
            "preflop": ["call", "raise", "call", "fold", "fold", "call"],
            "flop": ["check"],  # Only EP acts since everyone else folded preflop
            "turn": [],
            "river": []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_fold_to_aggression_closes_round(self):
        """Test that betting round can close when active players fold/call aggression"""
        input_data = {
            "EP": ["call", "fold"],     # calls preflop, folds to flop bet
            "MP": ["fold"],             # folds preflop
            "CO": ["call", "bet"],      # calls preflop, bets flop
            "BTN": ["call", "call"],    # calls preflop, calls flop bet
            "SB": ["fold"],             # folds preflop
            "BB": ["check", "call"]     # checks preflop, calls flop bet
        }
        
        expected_result = {
            "preflop": ["call", "fold", "call", "call", "fold", "check"],
            "flop": ["fold", "bet", "call", "call"],
            "turn": [],
            "river": []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_position_order_enforcement(self):
        """Test that actions follow correct position order"""
        input_data = {
            "EP": ["call"],
            "MP": ["raise"],
            "CO": ["fold"],
            "BTN": ["call"],
            "SB": ["fold"],
            "BB": ["call"]
        }
        
        # Should be: EP, MP, CO, BTN, SB, BB order
        expected_result = {
            "preflop": ["call", "raise", "fold", "call", "fold", "call"],
            "flop": [],
            "turn": [],
            "river": []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    def test_four_street_complete_game(self):
        """Test complete 4-street game with proper betting rounds"""
        input_data = {
            "EP": ["call", "check", "check", "check"],
            "MP": ["fold"],
            "CO": ["call", "check", "check", "check"],
            "BTN": ["call", "check", "check", "check"],
            "SB": ["fold"],
            "BB": ["check", "check", "check", "check"]
        }
        
        expected_result = {
            "preflop": ["call", "fold", "call", "call", "fold", "check"],
            "flop": ["check", "check", "check", "check"],
            "turn": ["check", "check", "check", "check"],
            "river": ["check", "check", "check", "check"]
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)


if __name__ == "__main__":
    unittest.main()