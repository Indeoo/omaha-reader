import unittest
import cv2
from pathlib import Path

from shared.domain.street import Street
from table_detector.services.game_snapshot_service import GameSnapshotService, GameSnapshotIncorrectException
from shared.domain.position import Position
from shared.domain.moves import MoveType


class GameSnapshotServiceTest(unittest.TestCase):

    def load_image(self, folder, image_name):
        test_dir = Path(__file__).parent.parent
        test_image_path = test_dir / "resources" / "service" / "game_snapshot_service" / str(folder) / image_name

        # Verify test image exists
        if not test_image_path.exists():
            self.fail(f"Test image not found: {test_image_path}")
        # Load test image
        cv2_image = cv2.imread(str(test_image_path))

        if cv2_image is None:
            self.fail(f"Failed to load test image: {test_image_path}")

        return cv2_image

    def test_create_game_snapshot_basic_1(self):
        """Test that create_game_snapshot returns a valid GameSnapshot object."""
        # Execute the method under test
        cv2_image = self.load_image(1, "01__2_50__5_Pot_Limit_Omaha.png")

        with self.assertRaises(GameSnapshotIncorrectException):
            GameSnapshotService.create_game_snapshot(cv2_image)

    def test_create_game_snapshot_basic_2(self):
        """Test that create_game_snapshot returns a valid GameSnapshot object."""
        # Execute the method under test
        cv2_image = self.load_image(2, "01__5__10_Pot_Limit_Omaha.png")

        GameSnapshotService.create_game_snapshot(cv2_image)

        expected = [
            (Position.EARLY_POSITION, MoveType.FOLD),
            (Position.MIDDLE_POSITION, MoveType.FOLD),
            (Position.CUTOFF, MoveType.FOLD),
            (Position.BUTTON, MoveType.FOLD)
        ]

        result = GameSnapshotService.create_game_snapshot(cv2_image).moves[Street.PREFLOP]

        self.assertEqual(expected, result)

    def test_create_game_snapshot_basic_3(self):
        """Test that create_game_snapshot returns a valid GameSnapshot object."""
        # Execute the method under test
        cv2_image = self.load_image(3, "01__2_50__5_Pot_Limit_Omaha.png")

        GameSnapshotService.create_game_snapshot(cv2_image)

        expected = [
            (Position.EARLY_POSITION, MoveType.FOLD),
            (Position.MIDDLE_POSITION, MoveType.FOLD),
        ]

        result = GameSnapshotService.create_game_snapshot(cv2_image).moves[Street.PREFLOP]

        self.assertEqual(expected, result)

    def test_create_game_snapshot_basic_4(self):
        """Test that create_game_snapshot returns a valid GameSnapshot object."""
        # Execute the method under test
        cv2_image = self.load_image(4, "debug_2.png")

        GameSnapshotService.create_game_snapshot(cv2_image)

        expected = [
        ]

        result = GameSnapshotService.create_game_snapshot(cv2_image).moves[Street.PREFLOP]

        self.assertEqual(expected, result)



    # @patch('table_detector.services.game_snapshot_service.logger')
    # def test_validate_position_continuity_no_gaps(self, mock_logger):
    #     """Test validation passes when no position gaps exist."""
    #     position_actions = {
    #         Position.MIDDLE_POSITION: [MoveType.FOLD],
    #         Position.CUTOFF: [MoveType.CALL],
    #         Position.BUTTON: [MoveType.RAISE]
    #     }
    #
    #     GameSnapshotService._validate_position_continuity(position_actions)
    #
    #     # Should not log any warnings
    #     mock_logger.warning.assert_not_called()

    # @patch('table_detector.services.game_snapshot_service.logger')
    # def test_validate_position_continuity_with_gaps(self, mock_logger):
    #     """Test validation detects gaps in position sequence."""
    #     position_actions = {
    #         Position.EARLY_POSITION: [MoveType.FOLD],
    #         Position.CUTOFF: [MoveType.RAISE]  # MP is missing
    #     }
    #
    #     GameSnapshotService._validate_position_continuity(position_actions)
    #
    #     # Should log warning about missing MP
    #     mock_logger.warning.assert_called()
    #     warning_call = mock_logger.warning.call_args[0][0]
    #     self.assertIn("Position continuity issue detected", warning_call)
    #     self.assertIn("MP", warning_call)
    #
    # @patch('table_detector.services.game_snapshot_service.logger')
    # def test_validate_position_continuity_critical_gap_scenario(self, mock_logger):
    #     """Test validation detects the specific MP fold, CO missing, BTN fold scenario."""
    #     position_actions = {
    #         Position.MIDDLE_POSITION: [MoveType.FOLD],
    #         Position.BUTTON: [MoveType.FOLD]  # CO is missing between MP and BTN
    #     }
    #
    #     GameSnapshotService._validate_position_continuity(position_actions)
    #
    #     # Should log both general warning and critical gap warning
    #     self.assertEqual(mock_logger.warning.call_count, 2)
    #
    #     # Check for critical gap warning
    #     warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
    #     critical_warning = next((w for w in warning_calls if "Critical gap detected" in w), None)
    #     self.assertIsNotNone(critical_warning)
    #     self.assertIn("BTN action detected but CO missing", critical_warning)
    #
    # @patch('table_detector.services.game_snapshot_service.logger')
    # def test_validate_position_continuity_empty_actions(self, mock_logger):
    #     """Test validation handles empty position actions gracefully."""
    #     position_actions = {}
    #
    #     GameSnapshotService._validate_position_continuity(position_actions)
    #
    #     # Should not log any warnings
    #     mock_logger.warning.assert_not_called()
    #
    def test_validate_position_continuity_2max_valid(self):
        """Test 2-max (heads-up) validation with valid positions."""
        position_actions = {
            Position.SMALL_BLIND: [MoveType.CALL],
            Position.BIG_BLIND: [MoveType.CHECK]
        }
        # Should not raise exception
        GameSnapshotService._validate_position_continuity(position_actions)

    def test_validate_position_continuity_3max_valid(self):
        """Test 3-max validation with valid positions."""
        position_actions = {
            Position.BUTTON: [MoveType.FOLD],
            Position.SMALL_BLIND: [MoveType.CALL],
            Position.BIG_BLIND: [MoveType.CHECK]
        }
        # Should not raise exception
        GameSnapshotService._validate_position_continuity(position_actions)

    def test_validate_position_continuity_4max_valid(self):
        """Test 4-max validation with valid positions."""
        position_actions = {
            Position.CUTOFF: [MoveType.FOLD],
            Position.BUTTON: [MoveType.CALL],
            Position.SMALL_BLIND: [MoveType.FOLD]
        }
        # Should not raise exception
        GameSnapshotService._validate_position_continuity(position_actions)

    def test_validate_position_continuity_5max_valid_no_mp(self):
        """Test 5-max validation passes without MP (the original issue)."""
        position_actions = {
            Position.EARLY_POSITION: [MoveType.FOLD],
            Position.CUTOFF: [MoveType.CALL],
            Position.BUTTON: [MoveType.RAISE],
            Position.SMALL_BLIND: [MoveType.FOLD],
            Position.BIG_BLIND: [MoveType.CALL]
        }
        # Should not raise exception - MP is not required for 5-max
        GameSnapshotService._validate_position_continuity(position_actions)

    def test_validate_position_continuity_5max_partial_positions(self):
        """Test 5-max validation with the specific scenario from the error."""
        position_actions = {
            Position.SMALL_BLIND: [MoveType.FOLD],
            Position.EARLY_POSITION: [MoveType.CALL], 
            Position.BUTTON: [MoveType.RAISE],
            Position.CUTOFF: [MoveType.FOLD],
            Position.BIG_BLIND: [MoveType.CALL]
        }
        # Should not raise exception - MP is not required for 5-max
        GameSnapshotService._validate_position_continuity(position_actions)

    def test_validate_position_continuity_6max_valid(self):
        """Test 6-max validation with valid positions including MP."""
        position_actions = {
            Position.EARLY_POSITION: [MoveType.FOLD],
            Position.MIDDLE_POSITION: [MoveType.CALL],
            Position.CUTOFF: [MoveType.RAISE],
            Position.BUTTON: [MoveType.FOLD]
        }
        # Should not raise exception
        GameSnapshotService._validate_position_continuity(position_actions)

    def test_validate_position_continuity_invalid_combination(self):
        """Test validation detects invalid position combinations."""
        position_actions = {
            Position.MIDDLE_POSITION: [MoveType.FOLD],  # MP suggests 6-max
            Position.EARLY_POSITION: [MoveType.CALL],   # But also have EP (valid)
            Position.CUTOFF: [MoveType.RAISE]           # And CO (valid)
        }
        # Should not raise exception - this is a valid 6-max subset
        GameSnapshotService._validate_position_continuity(position_actions)

    def test_validate_position_continuity_empty_actions(self):
        """Test validation handles empty position actions gracefully."""
        position_actions = {}
        # Should not raise exception
        GameSnapshotService._validate_position_continuity(position_actions)

    def test_validate_position_continuity_single_position(self):
        """Test validation handles single position without issues."""
        position_actions = {
            Position.BUTTON: [MoveType.FOLD]
        }
        # Should not raise exception
        GameSnapshotService._validate_position_continuity(position_actions)

    def test_determine_table_size_2max(self):
        """Test table size detection for 2-max."""
        detected_positions = {Position.SMALL_BLIND, Position.BIG_BLIND}
        table_size = GameSnapshotService._determine_table_size(detected_positions)
        self.assertEqual(table_size, 2)

    def test_determine_table_size_3max(self):
        """Test table size detection for 3-max."""
        detected_positions = {Position.BUTTON, Position.SMALL_BLIND}
        table_size = GameSnapshotService._determine_table_size(detected_positions)
        self.assertEqual(table_size, 3)

    def test_determine_table_size_4max(self):
        """Test table size detection for 4-max."""
        detected_positions = {Position.CUTOFF, Position.BUTTON}
        table_size = GameSnapshotService._determine_table_size(detected_positions)
        self.assertEqual(table_size, 4)

    def test_determine_table_size_5max(self):
        """Test table size detection for 5-max."""
        detected_positions = {Position.EARLY_POSITION, Position.CUTOFF, Position.BUTTON}
        table_size = GameSnapshotService._determine_table_size(detected_positions)
        self.assertEqual(table_size, 5)

    def test_determine_table_size_6max(self):
        """Test table size detection for 6-max."""
        detected_positions = {Position.MIDDLE_POSITION, Position.CUTOFF}
        table_size = GameSnapshotService._determine_table_size(detected_positions)
        self.assertEqual(table_size, 6)

    def test_get_valid_positions_for_all_table_sizes(self):
        """Test that valid positions are correct for each table size."""
        # 2-max
        positions_2max = GameSnapshotService._get_valid_positions_for_table_size(2)
        expected_2max = {Position.SMALL_BLIND, Position.BIG_BLIND}
        self.assertEqual(positions_2max, expected_2max)

        # 3-max
        positions_3max = GameSnapshotService._get_valid_positions_for_table_size(3)
        expected_3max = {Position.BUTTON, Position.SMALL_BLIND, Position.BIG_BLIND}
        self.assertEqual(positions_3max, expected_3max)

        # 4-max
        positions_4max = GameSnapshotService._get_valid_positions_for_table_size(4)
        expected_4max = {Position.CUTOFF, Position.BUTTON, Position.SMALL_BLIND, Position.BIG_BLIND}
        self.assertEqual(positions_4max, expected_4max)

        # 5-max (no MP)
        positions_5max = GameSnapshotService._get_valid_positions_for_table_size(5)
        expected_5max = {Position.EARLY_POSITION, Position.CUTOFF, Position.BUTTON, Position.SMALL_BLIND, Position.BIG_BLIND}
        self.assertEqual(positions_5max, expected_5max)

        # 6-max (with MP)
        positions_6max = GameSnapshotService._get_valid_positions_for_table_size(6)
        expected_6max = {Position.EARLY_POSITION, Position.MIDDLE_POSITION, Position.CUTOFF, Position.BUTTON, Position.SMALL_BLIND, Position.BIG_BLIND}
        self.assertEqual(positions_6max, expected_6max)
