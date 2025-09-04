import unittest

from shared.domain.moves import MoveType
from shared.domain.position import Position
from shared.domain.street import Street
from table_detector.services.omaha_action_processor import group_moves_by_street


class TestMovesByStreetWithExpectedResults(unittest.TestCase):


    def test_group_moves_by_street(self):
        expected = {
            Street.PREFLOP: [
                (Position.EARLY_POSITION, MoveType.RAISE),
                (Position.MIDDLE_POSITION, MoveType.CALL),
                (Position.CUTOFF, MoveType.FOLD),
                (Position.BUTTON, MoveType.CALL),
                (Position.SMALL_BLIND, MoveType.CALL),
            ],
            Street.FLOP: [
                (Position.SMALL_BLIND, MoveType.CHECK),
                (Position.BIG_BLIND, MoveType.CHECK),
                (Position.EARLY_POSITION, MoveType.CHECK),
            ],
            Street.TURN: [],
            Street.RIVER: []
        }

        input_data = {
            Position.EARLY_POSITION: [MoveType.RAISE, MoveType.CHECK],
            Position.MIDDLE_POSITION: [MoveType.CALL],
            Position.CUTOFF: [MoveType.FOLD],
            Position.BUTTON: [MoveType.CALL],
            Position.SMALL_BLIND: [MoveType.CALL, MoveType.CHECK],
            Position.BIG_BLIND: [MoveType.CALL, MoveType.CHECK],
        }

        result = group_moves_by_street(input_data)

        self.assertEqual(expected, result)
    #

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
            Position.BIG_BLIND: [MoveType.CHECK, MoveType.CHECK, MoveType.CALL, MoveType.CHECK]
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
                (Position.BIG_BLIND, MoveType.CHECK),
                (Position.EARLY_POSITION, MoveType.CHECK),
                (Position.CUTOFF, MoveType.BET),
                (Position.BUTTON, MoveType.CALL),
                (Position.BIG_BLIND, MoveType.CALL),
                (Position.EARLY_POSITION, MoveType.FOLD)
            ],
            Street.TURN: [
                (Position.BIG_BLIND, MoveType.CHECK),
                (Position.CUTOFF, MoveType.BET),
                (Position.BUTTON, MoveType.CALL)
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
            Position.EARLY_POSITION: [MoveType.CALL, MoveType.CALL, MoveType.FOLD],  # call, call MP's raise, fold to CO's bet
            Position.MIDDLE_POSITION: [MoveType.RAISE],  # raise preflop only
            Position.CUTOFF: [MoveType.CALL, MoveType.BET],  # call preflop, bet flop
            Position.BUTTON: [MoveType.CALL, MoveType.CALL],  # call preflop, call flop bet
            Position.SMALL_BLIND: [MoveType.FOLD],
            Position.BIG_BLIND: [MoveType.CALL, MoveType.CALL]  # call preflop, call flop bet
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
                (Position.CUTOFF, MoveType.BET),
                (Position.BUTTON, MoveType.CALL),
                (Position.BIG_BLIND, MoveType.CALL),
                (Position.EARLY_POSITION, MoveType.FOLD)
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
                (Position.BIG_BLIND, MoveType.CALL),
                (Position.EARLY_POSITION, MoveType.CHECK)
            ],
            Street.FLOP: [
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
                (Position.BUTTON, MoveType.CALL),
                (Position.BIG_BLIND, MoveType.CALL),
                (Position.CUTOFF, MoveType.BET),
                (Position.BUTTON, MoveType.CALL),
                (Position.BIG_BLIND, MoveType.CALL)
            ],
            Street.TURN: [
                (Position.CUTOFF, MoveType.RAISE)
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

    def test_button_raise_call_scenario(self):
        """Test scenario with BTN raise preflop, then BTN call on flop without prior aggression"""
        input_data = {
            Position.BUTTON: [MoveType.RAISE, MoveType.CALL],
            Position.SMALL_BLIND: [MoveType.CALL, MoveType.CHECK, MoveType.CALL],
            Position.BIG_BLIND: [MoveType.CALL, MoveType.CHECK, MoveType.CALL]
        }
        
        expected_result = {
            Street.PREFLOP: [
                (Position.BUTTON, MoveType.RAISE),
                (Position.SMALL_BLIND, MoveType.CALL),
                (Position.BIG_BLIND, MoveType.CALL)
            ],
            Street.FLOP: [
                (Position.SMALL_BLIND, MoveType.CHECK),
                (Position.BIG_BLIND, MoveType.CHECK),
                (Position.BUTTON, MoveType.BET),
                (Position.SMALL_BLIND, MoveType.CALL),
                (Position.BIG_BLIND, MoveType.CALL)
            ],
            Street.TURN: [

            ],
            Street.RIVER: []
        }
        
        result = group_moves_by_street(input_data)
        self.assertEqual(result, expected_result)

    # Note: Complex poker rule tests have been moved to omaha_game_test.py
    # This file now focuses on integration testing of the group_moves_by_street adapter function
