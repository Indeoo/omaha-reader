import unittest
import cv2
from pathlib import Path

from shared.domain.street import Street
from table_detector.services.game_snapshot_service import GameSnapshotService
from table_detector.domain.omaha_game import InvalidActionError
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
        """Test that create_game_snapshot raises InvalidActionError due to invalid poker action sequence."""
        # Execute the method under test
        cv2_image = self.load_image(1, "01__2_50__5_Pot_Limit_Omaha.png")

        with self.assertRaises(InvalidActionError):
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

    def test_create_game_snapshot_basic_5(self):
        """Test that create_game_snapshot returns a valid GameSnapshot object."""
        # Execute the method under test
        cv2_image = self.load_image(5, "debug_3.png")

        GameSnapshotService.create_game_snapshot(cv2_image)

        expected = [
            (Position.EARLY_POSITION, MoveType.RAISE)
        ]

        result = GameSnapshotService.create_game_snapshot(cv2_image).moves[Street.PREFLOP]

        self.assertEqual(expected, result)

    def test_create_game_snapshot_basic_6(self):
        """Test that create_game_snapshot returns a valid GameSnapshot object."""
        # Execute the method under test
        cv2_image = self.load_image(6, "debug_1.png")

        GameSnapshotService.create_game_snapshot(cv2_image)

        expected = {
            Street.PREFLOP: [
                (Position.EARLY_POSITION, MoveType.RAISE),
                (Position.MIDDLE_POSITION, MoveType.CALL),
                (Position.CUTOFF, MoveType.FOLD),
                (Position.BUTTON, MoveType.CALL),
                (Position.SMALL_BLIND, MoveType.CALL),
                (Position.BIG_BLIND, MoveType.CALL),
            ],
            Street.FLOP: [
                (Position.EARLY_POSITION, MoveType.CHECK),
                (Position.SMALL_BLIND, MoveType.CHECK),
                (Position.BIG_BLIND, MoveType.CHECK),
            ],
            Street.TURN: [],
            Street.RIVER: []
        }

        result = GameSnapshotService.create_game_snapshot(cv2_image).moves

        self.assertEqual(expected, result)

    def test_create_game_snapshot_basic_7(self):
        """Test that create_game_snapshot returns a valid GameSnapshot object."""
        # Execute the method under test
        cv2_image = self.load_image(7, "01__0_02__0_05_Pot_Limit_Omaha.png")

        GameSnapshotService.create_game_snapshot(cv2_image)

        # expected = {
        #     Street.PREFLOP: [
        #         (Position.EARLY_POSITION, MoveType.RAISE),
        #         (Position.MIDDLE_POSITION, MoveType.CALL),
        #         (Position.CUTOFF, MoveType.FOLD),
        #         (Position.BUTTON, MoveType.CALL),
        #         (Position.SMALL_BLIND, MoveType.CALL),
        #         (Position.BIG_BLIND, MoveType.CALL),
        #     ],
        #     Street.FLOP: [
        #         (Position.EARLY_POSITION, MoveType.CHECK),
        #         (Position.SMALL_BLIND, MoveType.CHECK),
        #         (Position.BIG_BLIND, MoveType.CHECK),
        #     ],
        #     Street.TURN: [],
        #     Street.RIVER: []
        # }

        result = GameSnapshotService.create_game_snapshot(cv2_image).moves
        print(result)

        #self.assertEqual(expected, result)

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

    def test_infer_missing_position_no_positions_detected(self):
        """Test position inference when no positions are detected."""

        detected_positions = {}

        # Test inference returns None when no context available
        inferred = GameSnapshotService._infer_missing_position(detected_positions)
        self.assertIsNone(inferred)
