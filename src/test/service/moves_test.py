import unittest
from src.core.service.moves_by_street import group_moves_by_street, group_moves_by_street_simple


class TestMovesByStreet(unittest.TestCase):
    
    def setUp(self):
        """Set up test data"""
        # Test data 1: Standard game with multiple betting rounds
        self.test_data_1 = {
            "EP": ["call", "raise", "raise", "call"],
            "MP": ["fold"],
            "CO": ["call", "call", "call", "fold"],
            "BTN": ["call", "call", "check", "check"],
            "SB": ["fold"],
            "BB": ["raise", "bet", "bet", "bet"],
        }

        # Test data 2: Game with extensive preflop action
        self.test_data_2 = {
            "EP": ["call", "fold"],  # Call open, fold to 3-bet
            "MP": ["fold"],
            "CO": ["fold"],
            "BTN": ["raise", "raise", "call"],  # 3-bet, 5-bet, call 6-bet
            "SB": ["fold"],
            "BB": ["raise", "raise", "raise"],  # Open, 4-bet, 6-bet
        }

        # Test data 3: Heads-up battle
        self.test_data_3 = {
            "SB": ["fold"],
            "BB": ["fold"],
            "EP": ["fold"],
            "MP": ["fold"],
            "CO": ["call", "raise", "call", "call", "raise", "raise", "call"],
            "BTN": ["raise", "call", "bet", "raise", "call", "check", "bet"]
        }

        # Test data 4: Complex multi-street action
        self.test_data_4 = {
            "SB": ["raise", "bet", "check", "bet", "bet", "bet"],
            "BB": ["fold"],
            "EP": ["call", "check", "raise", "raise", "raise", "raise"],
            "MP": ["fold"],
            "CO": ["call", "check", "call", "call", "call", "call"],
            "BTN": ["call", "check", "check", "call", "call", "fold"]
        }

        # Test data 5: Check-fest
        self.test_data_5 = {
            "SB": ["check", "check", "check", "check"],
            "BB": ["check", "check", "check", "check"],
            "EP": ["check", "check", "check", "check"],
            "MP": ["fold"],
            "CO": ["fold"],
            "BTN": ["check", "check", "check", "check"]
        }

    def test_standard_game(self):
        """Test standard game with multiple betting rounds"""
        result = group_moves_by_street(self.test_data_1)
        
        # Verify result structure
        self.assertIsInstance(result, dict)
        self.assertIn("preflop", result)
        
        # Verify that all moves are grouped
        total_moves_input = sum(len(moves) for moves in self.test_data_1.values())
        total_moves_output = sum(len(moves) for moves in result.values())
        self.assertEqual(total_moves_input, total_moves_output)

    def test_heavy_preflop_action(self):
        """Test game with extensive preflop action"""
        result = group_moves_by_street(self.test_data_2)
        
        # Verify result structure
        self.assertIsInstance(result, dict)
        self.assertIn("preflop", result)
        
        # Verify that all moves are grouped
        total_moves_input = sum(len(moves) for moves in self.test_data_2.values())
        total_moves_output = sum(len(moves) for moves in result.values())
        self.assertEqual(total_moves_input, total_moves_output)

    def test_heads_up_battle(self):
        """Test heads-up battle scenario"""
        result = group_moves_by_street(self.test_data_3)
        
        # Verify result structure
        self.assertIsInstance(result, dict)
        
        # Verify that all moves are grouped
        total_moves_input = sum(len(moves) for moves in self.test_data_3.values())
        total_moves_output = sum(len(moves) for moves in result.values())
        self.assertEqual(total_moves_input, total_moves_output)

    def test_complex_multi_street_action(self):
        """Test complex multi-street action"""
        result = group_moves_by_street(self.test_data_4)
        
        # Verify result structure
        self.assertIsInstance(result, dict)
        
        # Verify that all moves are grouped
        total_moves_input = sum(len(moves) for moves in self.test_data_4.values())
        total_moves_output = sum(len(moves) for moves in result.values())
        self.assertEqual(total_moves_input, total_moves_output)

    def test_check_fest(self):
        """Test scenario with mostly checks"""
        result = group_moves_by_street(self.test_data_5)
        
        # Verify result structure
        self.assertIsInstance(result, dict)
        
        # Verify that all moves are grouped
        total_moves_input = sum(len(moves) for moves in self.test_data_5.values())
        total_moves_output = sum(len(moves) for moves in result.values())
        self.assertEqual(total_moves_input, total_moves_output)

    def test_group_moves_by_street_simple(self):
        """Test simple approach with standard game"""
        result = group_moves_by_street_simple(self.test_data_1)
        
        # Verify result structure
        self.assertIsInstance(result, dict)
        
        # Verify that all moves are grouped
        total_moves_input = sum(len(moves) for moves in self.test_data_1.values())
        total_moves_output = sum(len(moves) for moves in result.values())
        self.assertEqual(total_moves_input, total_moves_output)

    def test_empty_input(self):
        """Test with empty input"""
        result = group_moves_by_street({})
        self.assertIsInstance(result, dict)

    def test_single_player_fold(self):
        """Test with single player folding"""
        test_data = {"SB": ["fold"]}
        result = group_moves_by_street(test_data)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(sum(len(moves) for moves in result.values()), 1)

    def test_return_type_consistency(self):
        """Test that both functions return consistent types"""
        result_1 = group_moves_by_street(self.test_data_1)
        result_2 = group_moves_by_street_simple(self.test_data_1)
        
        self.assertIsInstance(result_1, dict)
        self.assertIsInstance(result_2, dict)
        
        # Both should have string keys and list values
        for street, moves in result_1.items():
            self.assertIsInstance(street, str)
            self.assertIsInstance(moves, list)
            
        for street, moves in result_2.items():
            self.assertIsInstance(street, str)
            self.assertIsInstance(moves, list)
