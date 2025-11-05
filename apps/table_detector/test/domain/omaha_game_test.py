import unittest

from shared.domain.moves import MoveType
from table_detector.domain.omaha_engine import OmahaEngine, InvalidPositionSequenceError
from shared.domain.position import Position
from shared.domain.street import Street


class TestOmahaEngine(unittest.TestCase):
    
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
    
    def test_constructor_single_player_raises_error(self):
        """Test that game initialization fails with only one player"""
        with self.assertRaises(ValueError) as context:
            OmahaEngine(1)
        
        self.assertIn("Need at least 2 players", str(context.exception))
    
    def test_constructor_initializes_moves_by_street(self):
        """Test that moves_by_street is properly initialized"""
        game = OmahaEngine(6)
        
        moves_by_street = game. get_moves_by_street()
        
        # Check all streets are initialized
        self.assertIn(Street.PREFLOP, moves_by_street)
        self.assertIn(Street.FLOP, moves_by_street)
        self.assertIn(Street.TURN, moves_by_street)
        self.assertIn(Street.RIVER, moves_by_street)
        
        # Check all streets start empty
        for street in moves_by_street.values():
            self.assertEqual(street, [])

    # === ACTION PROCESSING TESTS ===
    
    def test_process_action_multiple_players(self):
        """Test processing actions from multiple players"""
        game = OmahaEngine(6)
        
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
        game = OmahaEngine(6)
        
        self.assertEqual(game.get_current_street(), Street.PREFLOP)
    
    def test_actions_recorded_on_correct_street(self):
        """Test that actions are recorded on the current street"""
        game = OmahaEngine(6)
        
        # Test valid action sequence - should succeed
        game.process_action(Position.EARLY_POSITION, MoveType.FOLD)
        game.process_action(Position.MIDDLE_POSITION, MoveType.CALL)
        
        moves = game.get_moves_by_street()
        
        # Verify actions are recorded on current street (preflop)
        self.assertEqual(len(moves[Street.PREFLOP]), 2)
        self.assertEqual(moves[Street.PREFLOP][0], (Position.EARLY_POSITION, MoveType.FOLD))
        self.assertEqual(moves[Street.PREFLOP][1], (Position.MIDDLE_POSITION, MoveType.CALL))
        
        # Other streets should be empty
        self.assertEqual(moves[Street.FLOP], [])
        self.assertEqual(moves[Street.TURN], [])
        self.assertEqual(moves[Street.RIVER], [])
        
        # Test invalid position sequence - should raise error
        with self.assertRaises(InvalidPositionSequenceError):
            game.process_action(Position.BUTTON, MoveType.CALL)  # Wrong position order

    # === MOVE HISTORY TESTS ===

    def test_move_history_ordering(self):
        """Test that moves are stored in chronological order"""
        game = OmahaEngine(6)
        
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
    
    # === INTEGRATION TESTS ===
    
    def test_complete_preflop_scenario(self):
        """Test a complete preflop betting round"""
        game = OmahaEngine(6)
        
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
        game = OmahaEngine(2)
        
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
        game = OmahaEngine(6)
        
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
        game = OmahaEngine(6)
        
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

    # === GAME END SCENARIOS ===

    def test_heads_up_all_in_scenario(self):
        """Test heads-up all-in scenario"""
        game = OmahaEngine(2)
        
        # Simulate all-in scenario
        game.process_action(Position.SMALL_BLIND, MoveType.RAISE)  # SB raises
        game.process_action(Position.BIG_BLIND, MoveType.RAISE)   # BB re-raises (all-in)
        game.process_action(Position.SMALL_BLIND, MoveType.CALL)  # SB calls all-in
        
        moves = game.get_moves_by_street()
        
        expected_moves = [
            (Position.SMALL_BLIND, MoveType.RAISE),
            (Position.BIG_BLIND, MoveType.RAISE),
            (Position.SMALL_BLIND, MoveType.CALL)
        ]
        
        self.assertEqual(moves[Street.PREFLOP], expected_moves)

    # === COMPLEX POSITION COMBINATION TESTS ===

    def test_three_player_game(self):
        """Test 3-player game dynamics"""
        three_player_positions = [
            Position.SMALL_BLIND,
            Position.BIG_BLIND,
            Position.BUTTON
        ]
        
        game = OmahaEngine(3)
        
        # Test action processing
        game.process_action(Position.BUTTON, MoveType.CALL)
        game.process_action(Position.SMALL_BLIND, MoveType.RAISE)
        game.process_action(Position.BIG_BLIND, MoveType.CALL)
        game.process_action(Position.BUTTON, MoveType.FOLD)
        
        moves = game.get_moves_by_street()
        expected_moves = [
            (Position.BUTTON, MoveType.CALL),
            (Position.SMALL_BLIND, MoveType.RAISE),
            (Position.BIG_BLIND, MoveType.CALL),
            (Position.BUTTON, MoveType.FOLD)
        ]
        
        self.assertEqual(moves[Street.PREFLOP], expected_moves)

    def test_multiple_player_counts(self):
        """Test game functionality with different player counts (parameterized test)"""
        test_cases = [
            {
                'player_count': 2,
                'positions': [Position.SMALL_BLIND, Position.BIG_BLIND],
                'actions': [
                    (Position.SMALL_BLIND, MoveType.CALL),
                    (Position.BIG_BLIND, MoveType.CHECK)
                ]
            },
            {
                'player_count': 4,
                'positions': [Position.SMALL_BLIND, Position.BIG_BLIND, Position.CUTOFF, Position.BUTTON],
                'actions': [
                    (Position.CUTOFF, MoveType.RAISE),
                    (Position.BUTTON, MoveType.CALL),
                    (Position.SMALL_BLIND, MoveType.FOLD),
                    (Position.BIG_BLIND, MoveType.CALL)
                ]
            },
            {
                'player_count': 5,
                'positions': [Position.SMALL_BLIND, Position.BIG_BLIND, Position.EARLY_POSITION, Position.CUTOFF, Position.BUTTON],
                'actions': [
                    (Position.EARLY_POSITION, MoveType.FOLD),
                    (Position.CUTOFF, MoveType.CALL),
                    (Position.BUTTON, MoveType.RAISE),
                    (Position.SMALL_BLIND, MoveType.FOLD),
                    (Position.BIG_BLIND, MoveType.CALL)
                ]
            }
        ]
        
        for test_case in test_cases:
            with self.subTest(player_count=test_case['player_count']):
                positions = test_case['positions']
                actions = test_case['actions']
                
                game = OmahaEngine(len(positions))

                # Test action processing
                for position, action in actions:
                    game.process_action(position, action)
                
                moves = game.get_moves_by_street()
                self.assertEqual(len(moves[Street.PREFLOP]), len(actions))
                self.assertEqual(moves[Street.PREFLOP], actions)

    # === EDGE CASE TESTS ===

    # === INTEGRATION SCENARIOS ===

    # def test_position_order_consistency(self):
    #     """Test that position order is maintained consistently across different game sizes"""
    #     position_sets = [
    #         # 3-handed
    #         [Position.SMALL_BLIND, Position.BIG_BLIND, Position.BUTTON],
    #         # 4-handed
    #         [Position.SMALL_BLIND, Position.BIG_BLIND, Position.CUTOFF, Position.BUTTON],
    #         # 6-handed (full)
    #         6
    #     ]
    #
    #     for positions in position_sets:
    #         with self.subTest(player_count=len(positions)):
    #             game = OmahaGame(positions)
    #
    #             # Test that each position maps to a unique index
    #             indices = set(game.position_to_index.values())
    #             self.assertEqual(len(indices), len(positions))
    #
    #             # Test that indices are consecutive starting from 0
    #             expected_indices = set(range(len(positions)))
    #             self.assertEqual(indices, expected_indices)


    # === MULTI-STREET TRANSITION TESTS ===

    def test_automatic_flop_transition(self):
        """Test automatic transition from preflop to flop with community cards"""
        game = OmahaEngine(3)
        
        # Define action sequence that transitions from preflop to flop
        actions = [
            # Preflop: Complete betting round to trigger flop transition
            (Position.BUTTON, MoveType.CALL),
            (Position.SMALL_BLIND, MoveType.CALL),
            (Position.BIG_BLIND, MoveType.CHECK),
            
            # Flop: First action on flop to verify transition worked
            (Position.SMALL_BLIND, MoveType.CHECK)
        ]
        
        # Process all actions
        for position, action in actions:
            game.process_action(position, action)
        
        # Expected moves showing preflop completion and flop transition
        expected_moves = {
            Street.PREFLOP: [
                (Position.BUTTON, MoveType.CALL),
                (Position.SMALL_BLIND, MoveType.CALL),
                (Position.BIG_BLIND, MoveType.CHECK)
            ],
            Street.FLOP: [
                (Position.SMALL_BLIND, MoveType.CHECK)
            ],
            Street.TURN: [],
            Street.RIVER: []
        }
        
        # Verify actual moves match expected moves
        actual_moves = game.get_moves_by_street()
        self.assertEqual(actual_moves, expected_moves)

    def test_automatic_turn_transition(self):
        """Test automatic transition through flop to turn"""
        game = OmahaEngine(3)
        
        # Define action sequence that progresses from preflop through flop to turn
        actions = [
            # Preflop: Complete betting round
            (Position.BUTTON, MoveType.CALL),
            (Position.SMALL_BLIND, MoveType.CALL),
            (Position.BIG_BLIND, MoveType.CHECK),
            
            # Flop: Complete betting round with action to keep game alive
            (Position.SMALL_BLIND, MoveType.BET),
            (Position.BIG_BLIND, MoveType.CALL),
            (Position.BUTTON, MoveType.CALL),
            
            # Turn: First action on turn to verify transition worked
            (Position.SMALL_BLIND, MoveType.CHECK)
        ]
        
        # Process all actions
        for position, action in actions:
            game.process_action(position, action)
        
        # Expected moves showing progression through preflop, flop, to turn
        expected_moves = {
            Street.PREFLOP: [
                (Position.BUTTON, MoveType.CALL),
                (Position.SMALL_BLIND, MoveType.CALL),
                (Position.BIG_BLIND, MoveType.CHECK)
            ],
            Street.FLOP: [
                (Position.SMALL_BLIND, MoveType.BET),
                (Position.BIG_BLIND, MoveType.CALL),
                (Position.BUTTON, MoveType.CALL)
            ],
            Street.TURN: [
                (Position.SMALL_BLIND, MoveType.CHECK)
            ],
            Street.RIVER: []
        }
        
        # Verify actual moves match expected moves
        actual_moves = game.get_moves_by_street()
        self.assertEqual(actual_moves, expected_moves)

    def test_automatic_river_transition(self):
        """Test automatic transition through all streets to river"""
        game = OmahaEngine(3)
        
        # Define action sequence that progresses through all streets to river
        actions = [
            # Preflop: Complete betting round
            (Position.BUTTON, MoveType.CALL),
            (Position.SMALL_BLIND, MoveType.CALL),
            (Position.BIG_BLIND, MoveType.CHECK),
            
            # Flop: Betting action to keep game alive
            (Position.SMALL_BLIND, MoveType.BET),
            (Position.BIG_BLIND, MoveType.CALL),
            (Position.BUTTON, MoveType.CALL),
            
            # Turn: Betting action to keep game alive and reach river
            (Position.SMALL_BLIND, MoveType.CHECK),
            (Position.BIG_BLIND, MoveType.BET),
            (Position.BUTTON, MoveType.CALL),
            (Position.SMALL_BLIND, MoveType.CALL),
            
            # River: First action on river to verify transition worked
            (Position.SMALL_BLIND, MoveType.CHECK)
        ]
        
        # Process all actions
        for position, action in actions:
            game.process_action(position, action)
        
        # Expected moves showing progression through all four streets
        expected_moves = {
            Street.PREFLOP: [
                (Position.BUTTON, MoveType.CALL),
                (Position.SMALL_BLIND, MoveType.CALL),
                (Position.BIG_BLIND, MoveType.CHECK)
            ],
            Street.FLOP: [
                (Position.SMALL_BLIND, MoveType.BET),
                (Position.BIG_BLIND, MoveType.CALL),
                (Position.BUTTON, MoveType.CALL)
            ],
            Street.TURN: [
                (Position.SMALL_BLIND, MoveType.CHECK),
                (Position.BIG_BLIND, MoveType.BET),
                (Position.BUTTON, MoveType.CALL),
                (Position.SMALL_BLIND, MoveType.CALL)
            ],
            Street.RIVER: [
                (Position.SMALL_BLIND, MoveType.CHECK)
            ]
        }
        
        # Verify actual moves match expected moves
        actual_moves = game.get_moves_by_street()
        self.assertEqual(actual_moves, expected_moves)

    def test_street_transition_with_eliminations(self):
        """Test realistic scenario with player eliminations across streets"""
        game = OmahaEngine(6)
        
        # Define action sequence with eliminations
        actions = [
            # Preflop: Some folds, some calls/raises (EP, BTN, SB fold; MP, CO, BB remain)
            (Position.EARLY_POSITION, MoveType.FOLD),
            (Position.MIDDLE_POSITION, MoveType.CALL),
            (Position.CUTOFF, MoveType.RAISE),
            (Position.BUTTON, MoveType.FOLD),
            (Position.SMALL_BLIND, MoveType.FOLD),
            (Position.BIG_BLIND, MoveType.CALL),
            (Position.MIDDLE_POSITION, MoveType.CALL),
            
            # Flop: Remaining players (SB already folded, so BB acts first, then MP, then CO)
            (Position.BIG_BLIND, MoveType.CHECK),
            (Position.MIDDLE_POSITION, MoveType.BET),
            (Position.CUTOFF, MoveType.CALL),
            (Position.BIG_BLIND, MoveType.CALL),

            # Turn: MP folds, leaving only BB and CO
            (Position.BIG_BLIND, MoveType.BET),
            (Position.MIDDLE_POSITION, MoveType.FOLD),
            (Position.CUTOFF, MoveType.CALL),
            
            # River: Heads-up between BB and CO
            (Position.BIG_BLIND, MoveType.BET),
            (Position.CUTOFF, MoveType.CALL)
        ]
        
        # Process all actions
        for position, action in actions:
            game.process_action(position, action)
        
        # Expected moves showing eliminations across streets
        expected_moves = {
            Street.PREFLOP: [
                (Position.EARLY_POSITION, MoveType.FOLD),
                (Position.MIDDLE_POSITION, MoveType.CALL),
                (Position.CUTOFF, MoveType.RAISE),
                (Position.BUTTON, MoveType.FOLD),
                (Position.SMALL_BLIND, MoveType.FOLD),
                (Position.BIG_BLIND, MoveType.CALL),
                (Position.MIDDLE_POSITION, MoveType.CALL)
            ],
            Street.FLOP: [
                (Position.BIG_BLIND, MoveType.CHECK),
                (Position.MIDDLE_POSITION, MoveType.BET),
                (Position.CUTOFF, MoveType.CALL),
                (Position.BIG_BLIND, MoveType.CALL),
            ],
            Street.TURN: [
                (Position.BIG_BLIND, MoveType.BET),
                (Position.MIDDLE_POSITION, MoveType.FOLD),
                (Position.CUTOFF, MoveType.CALL),
            ],
            Street.RIVER: [
                (Position.BIG_BLIND, MoveType.BET),
                (Position.CUTOFF, MoveType.CALL)
            ]
        }
        
        # Verify actual moves match expected moves
        actual_moves = game.get_moves_by_street()
        self.assertEqual(actual_moves, expected_moves)

