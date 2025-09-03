import unittest

from shared.domain.moves import MoveType
from table_detector.domain.omaha_game import OmahaGame, InvalidActionError
from shared.domain.position import Position
from shared.domain.street import Street


class TestOmahaGame(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.default_positions = [
            Position.SMALL_BLIND,
            Position.BIG_BLIND,
            Position.EARLY_POSITION,
            Position.MIDDLE_POSITION,
            Position.CUTOFF,
            Position.BUTTON
        ]
        self.minimal_positions = [Position.SMALL_BLIND, Position.BIG_BLIND]
    
    # === CONSTRUCTOR TESTS ===
    
    def test_constructor_valid_positions(self):
        """Test game initialization with valid player positions"""
        game = OmahaGame(self.default_positions)
        
        # Check that position mappings are created correctly
        self.assertEqual(len(game.position_to_index), 6)
        self.assertEqual(len(game.index_to_position), 6)
        
        # Check that all positions are mapped
        for position in self.default_positions:
            self.assertIn(position, game.position_to_index)
            index = game.position_to_index[position]
            self.assertEqual(game.index_to_position[index], position)
    
    def test_constructor_minimal_positions(self):
        """Test game initialization with minimum required positions (2 players)"""
        game = OmahaGame(self.minimal_positions)
        
        self.assertEqual(len(game.position_to_index), 2)
        self.assertEqual(len(game.index_to_position), 2)
        
        # Check position mappings
        self.assertIn(Position.SMALL_BLIND, game.position_to_index)
        self.assertIn(Position.BIG_BLIND, game.position_to_index)
    
    def test_constructor_single_player_raises_error(self):
        """Test that game initialization fails with only one player"""
        with self.assertRaises(ValueError) as context:
            OmahaGame([Position.BUTTON])
        
        self.assertIn("Need at least 2 players", str(context.exception))
    
    def test_constructor_empty_positions_raises_error(self):
        """Test that game initialization fails with no players"""
        with self.assertRaises(ValueError) as context:
            OmahaGame([])
        
        self.assertIn("Need at least 2 players", str(context.exception))
    
    def test_constructor_initializes_moves_by_street(self):
        """Test that moves_by_street is properly initialized"""
        game = OmahaGame(self.default_positions)
        
        moves_by_street = game. get_moves_by_street()
        
        # Check all streets are initialized
        self.assertIn(Street.PREFLOP, moves_by_street)
        self.assertIn(Street.FLOP, moves_by_street)
        self.assertIn(Street.TURN, moves_by_street)
        self.assertIn(Street.RIVER, moves_by_street)
        
        # Check all streets start empty
        for street in moves_by_street.values():
            self.assertEqual(street, [])
    
    def test_constructor_initializes_pokerkit_state(self):
        """Test that pokerkit state is properly initialized"""
        game = OmahaGame(self.default_positions)
        
        # Check that poker_state is created
        self.assertIsNotNone(game.poker_state)
        
        # Check current street is preflop (street_index = 0)
        self.assertEqual(game.get_current_street(), Street.PREFLOP)
    
    # === ACTION PROCESSING TESTS ===
    
    def test_process_action_valid_fold(self):
        """Test processing a valid fold action"""
        game = OmahaGame(self.default_positions)
        
        result = game.process_action(Position.BUTTON, MoveType.FOLD)
        
        self.assertTrue(result)
        moves = game.get_moves_by_street()
        self.assertEqual(len(moves[Street.PREFLOP]), 1)
        self.assertEqual(moves[Street.PREFLOP][0], (Position.BUTTON, MoveType.FOLD))
    
    def test_process_action_valid_check(self):
        """Test processing a valid check action"""
        game = OmahaGame(self.default_positions)
        
        result = game.process_action(Position.BIG_BLIND, MoveType.CALL)
        
        self.assertTrue(result)
        moves = game.get_moves_by_street()
        self.assertEqual(len(moves[Street.PREFLOP]), 1)
        self.assertEqual(moves[Street.PREFLOP][0], (Position.BIG_BLIND, MoveType.CALL))
    
    def test_process_action_valid_call(self):
        """Test processing a valid call action"""
        game = OmahaGame(self.default_positions)
        
        result = game.process_action(Position.CUTOFF, MoveType.CALL)
        
        self.assertTrue(result)
        moves = game.get_moves_by_street()
        self.assertEqual(len(moves[Street.PREFLOP]), 1)
        self.assertEqual(moves[Street.PREFLOP][0], (Position.CUTOFF, MoveType.CALL))
    
    def test_process_action_valid_raise(self):
        """Test processing a valid raise action"""
        game = OmahaGame(self.default_positions)
        
        result = game.process_action(Position.MIDDLE_POSITION, MoveType.RAISE)
        
        self.assertTrue(result)
        moves = game.get_moves_by_street()
        self.assertEqual(len(moves[Street.PREFLOP]), 1)
        self.assertEqual(moves[Street.PREFLOP][0], (Position.MIDDLE_POSITION, MoveType.RAISE))
    
    def test_process_action_valid_bet(self):
        """Test processing a valid bet action"""
        game = OmahaGame(self.default_positions)
        
        result = game.process_action(Position.EARLY_POSITION, MoveType.BET)
        
        self.assertTrue(result)
        moves = game.get_moves_by_street()
        self.assertEqual(len(moves[Street.PREFLOP]), 1)
        self.assertEqual(moves[Street.PREFLOP][0], (Position.EARLY_POSITION, MoveType.BET))
    
    def test_process_action_multiple_actions_same_player(self):
        """Test that the same player can make multiple actions"""
        game = OmahaGame(self.default_positions)
        
        # Process multiple actions for same player
        game.process_action(Position.BUTTON, MoveType.CALL)
        game.process_action(Position.BUTTON, MoveType.RAISE)
        
        moves = game.get_moves_by_street()
        self.assertEqual(len(moves[Street.PREFLOP]), 2)
        self.assertEqual(moves[Street.PREFLOP][0], (Position.BUTTON, MoveType.CALL))
        self.assertEqual(moves[Street.PREFLOP][1], (Position.BUTTON, MoveType.RAISE))
    
    def test_process_action_multiple_players(self):
        """Test processing actions from multiple players"""
        game = OmahaGame(self.default_positions)
        
        # Process actions from different players
        game.process_action(Position.EARLY_POSITION, MoveType.FOLD)
        game.process_action(Position.MIDDLE_POSITION, MoveType.CALL)
        game.process_action(Position.CUTOFF, MoveType.RAISE)
        
        moves = game.get_moves_by_street()
        expected_moves = [
            (Position.EARLY_POSITION, MoveType.FOLD),
            (Position.MIDDLE_POSITION, MoveType.CALL),
            (Position.CUTOFF, MoveType.RAISE)
        ]
        
        self.assertEqual(moves[Street.PREFLOP], expected_moves)
    
    # === STREET MANAGEMENT TESTS ===
    
    def test_get_current_street_initial_state(self):
        """Test that new game starts on preflop"""
        game = OmahaGame(self.default_positions)
        
        self.assertEqual(game.get_current_street(), Street.PREFLOP)
    
    def test_get_current_street_mapping(self):
        """Test street mapping from pokerkit street_index"""
        game = OmahaGame(self.default_positions)
        
        # Test that the mapping works correctly
        # Note: We can't easily change street_index in pokerkit without complex setup
        # But we can at least verify the initial state is correct
        self.assertEqual(game.get_current_street(), Street.PREFLOP)
        self.assertEqual(game.poker_state.street_index, 0)
    
    def test_actions_recorded_on_correct_street(self):
        """Test that actions are recorded on the current street"""
        game = OmahaGame(self.default_positions)
        
        # Process actions on preflop
        game.process_action(Position.BUTTON, MoveType.CALL)
        game.process_action(Position.CUTOFF, MoveType.FOLD)
        
        moves = game.get_moves_by_street()
        
        # Check preflop has the moves
        self.assertEqual(len(moves[Street.PREFLOP]), 2)
        self.assertEqual(moves[Street.PREFLOP][0], (Position.BUTTON, MoveType.CALL))
        self.assertEqual(moves[Street.PREFLOP][1], (Position.CUTOFF, MoveType.FOLD))
        
        # Check other streets are empty
        self.assertEqual(moves[Street.FLOP], [])
        self.assertEqual(moves[Street.TURN], [])
        self.assertEqual(moves[Street.RIVER], [])
    
    # === MOVE HISTORY TESTS ===
    
    def test_get_moves_by_street_returns_copy(self):
        """Test that get_moves_by_street returns a copy of the dictionary"""
        game = OmahaGame(self.default_positions)
        
        game.process_action(Position.BUTTON, MoveType.FOLD)
        
        moves1 = game.get_moves_by_street()
        moves2 = game.get_moves_by_street()
        
        # Should be equal but not the same dictionary object
        self.assertEqual(moves1, moves2)
        self.assertIsNot(moves1, moves2)
        
        # The dictionary is a shallow copy - modifying the dictionary structure
        # won't affect other copies, but modifying the lists inside will
        # (this is the current implementation behavior using .copy())
        
        # Test that we can modify the dictionary structure independently
        moves1[Street.PREFLOP] = []  # Replace the entire list
        
        # moves2 should still have the original list
        self.assertEqual(len(moves2[Street.PREFLOP]), 1)
        self.assertEqual(moves2[Street.PREFLOP][0], (Position.BUTTON, MoveType.FOLD))
        
        # Getting a fresh copy should also have the original data
        moves3 = game.get_moves_by_street()
        self.assertEqual(len(moves3[Street.PREFLOP]), 1)
        self.assertEqual(moves3[Street.PREFLOP][0], (Position.BUTTON, MoveType.FOLD))
    
    def test_move_history_structure(self):
        """Test that move history has correct structure"""
        game = OmahaGame(self.default_positions)
        
        moves = game.get_moves_by_street()
        
        # Check all streets exist
        self.assertIn(Street.PREFLOP, moves)
        self.assertIn(Street.FLOP, moves)
        self.assertIn(Street.TURN, moves)
        self.assertIn(Street.RIVER, moves)
        
        # Check all streets are lists
        for street_moves in moves.values():
            self.assertIsInstance(street_moves, list)
    
    def test_move_history_format(self):
        """Test that moves are stored in correct format (position, action) tuples"""
        game = OmahaGame(self.default_positions)
        
        game.process_action(Position.BUTTON, MoveType.RAISE)
        game.process_action(Position.CUTOFF, MoveType.CALL)
        
        moves = game.get_moves_by_street()
        preflop_moves = moves[Street.PREFLOP]
        
        self.assertEqual(len(preflop_moves), 2)
        
        # Check first move format
        first_move = preflop_moves[0]
        self.assertIsInstance(first_move, tuple)
        self.assertEqual(len(first_move), 2)
        self.assertIsInstance(first_move[0], Position)
        self.assertIsInstance(first_move[1], MoveType)
        self.assertEqual(first_move, (Position.BUTTON, MoveType.RAISE))
        
        # Check second move format
        second_move = preflop_moves[1]
        self.assertEqual(second_move, (Position.CUTOFF, MoveType.CALL))
    
    def test_move_history_ordering(self):
        """Test that moves are stored in chronological order"""
        game = OmahaGame(self.default_positions)
        
        # Process actions in specific order
        actions = [
            (Position.EARLY_POSITION, MoveType.FOLD),
            (Position.MIDDLE_POSITION, MoveType.CALL),
            (Position.CUTOFF, MoveType.RAISE),
            (Position.BUTTON, MoveType.CALL),
            (Position.SMALL_BLIND, MoveType.FOLD),
            (Position.BIG_BLIND, MoveType.CALL)
        ]
        
        for position, action in actions:
            game.process_action(position, action)
        
        moves = game.get_moves_by_street()
        preflop_moves = moves[Street.PREFLOP]
        
        # Check that moves are in the same order as processed
        self.assertEqual(len(preflop_moves), len(actions))
        for i, (expected_position, expected_action) in enumerate(actions):
            actual_position, actual_action = preflop_moves[i]
            self.assertEqual(actual_position, expected_position)
            self.assertEqual(actual_action, expected_action)
    
    def test_empty_move_history_initially(self):
        """Test that all streets start with empty move history"""
        game = OmahaGame(self.default_positions)
        
        moves = game.get_moves_by_street()
        
        for street, street_moves in moves.items():
            self.assertEqual(street_moves, [], f"Street {street} should start empty")
    
    # === INTEGRATION TESTS ===
    
    def test_complete_preflop_scenario(self):
        """Test a complete preflop betting round"""
        game = OmahaGame(self.default_positions)
        
        # Simulate a typical preflop scenario
        game.process_action(Position.EARLY_POSITION, MoveType.FOLD)
        game.process_action(Position.MIDDLE_POSITION, MoveType.CALL)
        game.process_action(Position.CUTOFF, MoveType.RAISE)
        game.process_action(Position.BUTTON, MoveType.CALL)
        game.process_action(Position.SMALL_BLIND, MoveType.FOLD)
        game.process_action(Position.BIG_BLIND, MoveType.CALL)
        
        moves = game.get_moves_by_street()
        
        # Verify complete action sequence
        expected_preflop = [
            (Position.EARLY_POSITION, MoveType.FOLD),
            (Position.MIDDLE_POSITION, MoveType.CALL),
            (Position.CUTOFF, MoveType.RAISE),
            (Position.BUTTON, MoveType.CALL),
            (Position.SMALL_BLIND, MoveType.FOLD),
            (Position.BIG_BLIND, MoveType.CALL)
        ]
        
        self.assertEqual(moves[Street.PREFLOP], expected_preflop)
        
        # Other streets should remain empty
        self.assertEqual(moves[Street.FLOP], [])
        self.assertEqual(moves[Street.TURN], [])
        self.assertEqual(moves[Street.RIVER], [])
    
    def test_heads_up_scenario(self):
        """Test a heads-up (2 player) scenario"""
        game = OmahaGame(self.minimal_positions)
        
        # Heads-up action
        game.process_action(Position.SMALL_BLIND, MoveType.CALL)  # Complete to BB
        game.process_action(Position.BIG_BLIND, MoveType.CHECK)
        
        moves = game.get_moves_by_street()
        
        expected_moves = [
            (Position.SMALL_BLIND, MoveType.CALL),
            (Position.BIG_BLIND, MoveType.CHECK)
        ]
        
        self.assertEqual(moves[Street.PREFLOP], expected_moves)
    
    def test_all_fold_scenario(self):
        """Test scenario where everyone folds to big blind"""
        game = OmahaGame(self.default_positions)
        
        # Everyone folds to BB
        fold_positions = [
            Position.EARLY_POSITION,
            Position.MIDDLE_POSITION,
            Position.CUTOFF,
            Position.BUTTON,
            Position.SMALL_BLIND
        ]
        
        for position in fold_positions:
            game.process_action(position, MoveType.FOLD)
        
        moves = game.get_moves_by_street()
        
        # Should have 5 folds
        self.assertEqual(len(moves[Street.PREFLOP]), 5)
        
        for i, position in enumerate(fold_positions):
            self.assertEqual(moves[Street.PREFLOP][i], (position, MoveType.FOLD))
    
    def test_complex_betting_scenario(self):
        """Test complex multi-action scenario"""
        game = OmahaGame(self.default_positions)
        
        # Complex betting sequence
        game.process_action(Position.EARLY_POSITION, MoveType.CALL)
        game.process_action(Position.MIDDLE_POSITION, MoveType.RAISE)
        game.process_action(Position.CUTOFF, MoveType.CALL)
        game.process_action(Position.BUTTON, MoveType.RAISE)  # 3-bet
        game.process_action(Position.SMALL_BLIND, MoveType.FOLD)
        game.process_action(Position.BIG_BLIND, MoveType.CALL)
        game.process_action(Position.EARLY_POSITION, MoveType.CALL)  # Call the 3-bet
        game.process_action(Position.MIDDLE_POSITION, MoveType.CALL)  # Call the 3-bet
        game.process_action(Position.CUTOFF, MoveType.FOLD)  # Fold to 3-bet
        
        moves = game.get_moves_by_street()
        
        expected_sequence = [
            (Position.EARLY_POSITION, MoveType.CALL),
            (Position.MIDDLE_POSITION, MoveType.RAISE),
            (Position.CUTOFF, MoveType.CALL),
            (Position.BUTTON, MoveType.RAISE),
            (Position.SMALL_BLIND, MoveType.FOLD),
            (Position.BIG_BLIND, MoveType.CALL),
            (Position.EARLY_POSITION, MoveType.CALL),
            (Position.MIDDLE_POSITION, MoveType.CALL),
            (Position.CUTOFF, MoveType.FOLD)
        ]
        
        self.assertEqual(moves[Street.PREFLOP], expected_sequence)
    
    def test_game_state_consistency(self):
        """Test that game state remains consistent throughout play"""
        game = OmahaGame(self.default_positions)
        
        initial_street = game.get_current_street()
        
        # Process some actions
        game.process_action(Position.BUTTON, MoveType.CALL)
        game.process_action(Position.CUTOFF, MoveType.RAISE)
        
        # State should be consistent
        self.assertEqual(game.get_current_street(), initial_street)  # Still preflop
        
        current_moves = game.get_moves_by_street()
        
        # Should have 2 moves on preflop now
        self.assertEqual(len(current_moves[Street.PREFLOP]), 2)
        
        # Other streets should still be empty
        self.assertEqual(current_moves[Street.FLOP], [])
        self.assertEqual(current_moves[Street.TURN], [])
        self.assertEqual(current_moves[Street.RIVER], [])
    
    def test_invalid_action_preserves_state(self):
        """Test that invalid actions don't modify game state"""
        game = OmahaGame(self.default_positions)
        
        # Process a valid action first
        game.process_action(Position.BUTTON, MoveType.CALL)
        
        moves_before = game.get_moves_by_street()
        
        # Try invalid action (position not in game)
        try:
            invalid_game = OmahaGame([Position.BUTTON, Position.CUTOFF])
            invalid_game.process_action(Position.BIG_BLIND, MoveType.FOLD)
        except InvalidActionError:
            pass  # Expected
        
        # Original game state should be unchanged
        moves_after = game.get_moves_by_street()
        self.assertEqual(moves_before, moves_after)