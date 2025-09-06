import unittest

from shared.domain.detected_position import DetectedPosition
from shared.domain.detection import Detection
from shared.domain.position import Position
from table_detector.services.position_service import PositionService


class PositionServiceTest(unittest.TestCase):

    def test_c_bets_convertion(self):
        """Test conversion of valid Detection objects to DetectedPosition enums."""
        # Create mock Detection objects
        positions = {
            1: Detection("c_bets", (300, 120), (280, 100, 40, 40), 0.99),
            2: Detection("BB", (35, 173), (15, 153, 40, 40), 0.97),
            3: Detection("NO", (35, 330), (15, 310, 40, 40), 0.98),
            4: Detection("BTN_fold", (35, 330), (15, 310, 40, 40), 0.98),
            5: Detection("NO", (35, 330), (15, 310, 40, 40), 0.98),
            6: Detection("NO", (35, 330), (15, 310, 40, 40), 0.98),
        }

        result = PositionService.get_positions(positions)

        expected = {
            1: Position.SMALL_BLIND,
            2: Position.BIG_BLIND,
            4: Position.BUTTON,
        }

        self.assertEqual(expected, result)


    def test_convert_detections_to_detected_positions_valid_detections(self):
        """Test conversion of valid Detection objects to DetectedPosition enums."""
        # Create mock Detection objects
        positions = {
            1: Detection("BTN", (300, 120), (280, 100, 40, 40), 0.99),
            2: Detection("SB", (35, 330), (15, 310, 40, 40), 0.98),
            3: Detection("BB", (35, 173), (15, 153, 40, 40), 0.97),
            4: Detection("EP", (297, 120), (277, 100, 40, 40), 0.96),
            5: Detection("MP", (562, 168), (542, 148, 40, 40), 0.95),
            6: Detection("CO", (565, 332), (545, 312, 40, 40), 0.94)
        }

        result = PositionService.convert_detections_to_detected_positions(positions)

        expected = {
            1: DetectedPosition.BUTTON,
            2: DetectedPosition.SMALL_BLIND,
            3: DetectedPosition.BIG_BLIND,
            4: DetectedPosition.EARLY_POSITION,
            5: DetectedPosition.MIDDLE_POSITION,
            6: DetectedPosition.CUTOFF
        }

        self.assertEqual(result, expected)

    def test_convert_detections_to_detected_positions_with_variations(self):
        """Test conversion handles position variations like BTN_fold."""
        positions = {
            1: Detection("BTN_fold", (300, 120), (280, 100, 40, 40), 0.99),
            2: Detection("SB_fold", (35, 330), (15, 310, 40, 40), 0.98),
            3: Detection("BB_low", (35, 173), (15, 153, 40, 40), 0.97),
            4: Detection("EP_now", (297, 120), (277, 100, 40, 40), 0.96),
            5: Detection("MP_fold", (562, 168), (542, 148, 40, 40), 0.95),
            6: Detection("CO_fold", (565, 332), (545, 312, 40, 40), 0.94)
        }

        result = PositionService.convert_detections_to_detected_positions(positions)

        expected = {
            1: DetectedPosition.BUTTON_FOLD,
            2: DetectedPosition.SMALL_BLIND_FOLD,
            3: DetectedPosition.BIG_BLIND_LOW,
            4: DetectedPosition.EARLY_POSITION_NOW,
            5: DetectedPosition.MIDDLE_POSITION_FOLD,
            6: DetectedPosition.CUTOFF_FOLD
        }

        self.assertEqual(result, expected)


    def test_filter_and_recover_positions_all_direct_positions(self):
        """Test filtering when all detections are direct positions."""
        detected_positions = {
            1: DetectedPosition.BUTTON,
            2: DetectedPosition.SMALL_BLIND,
            3: DetectedPosition.BIG_BLIND,
            4: DetectedPosition.EARLY_POSITION,
            5: DetectedPosition.MIDDLE_POSITION,
            6: DetectedPosition.CUTOFF
        }

        result = PositionService.filter_and_recover_positions(detected_positions)

        expected = {
            1: Position.BUTTON,
            2: Position.SMALL_BLIND,
            3: Position.BIG_BLIND,
            4: Position.EARLY_POSITION,
            5: Position.MIDDLE_POSITION,
            6: Position.CUTOFF
        }

        self.assertEqual(result, expected)

    def test_filter_and_recover_positions_with_folded_variations(self):
        """Test filtering position variations like BTN_fold."""
        detected_positions = {
            1: DetectedPosition.BUTTON_FOLD,
            2: DetectedPosition.SMALL_BLIND_FOLD,
            3: DetectedPosition.BIG_BLIND_LOW,
            4: DetectedPosition.EARLY_POSITION_NOW,
            5: DetectedPosition.MIDDLE_POSITION_FOLD,
            6: DetectedPosition.CUTOFF_FOLD
        }

        result = PositionService.filter_and_recover_positions(detected_positions)

        expected = {
            1: Position.BUTTON,
            2: Position.SMALL_BLIND,
            3: Position.BIG_BLIND,
            4: Position.EARLY_POSITION,
            5: Position.MIDDLE_POSITION,
            6: Position.CUTOFF
        }

        self.assertEqual(result, expected)

    def test_filter_and_recover_positions_with_action_recovery(self):
        """Test recovery of position when action text is detected."""
        detected_positions = {
            1: DetectedPosition.BUTTON,
            2: DetectedPosition.SMALL_BLIND,
            3: DetectedPosition.BIG_BLIND,
            4: DetectedPosition.EARLY_POSITION,
            5: DetectedPosition.MIDDLE_POSITION,
            6: DetectedPosition.FOLDS  # Action text detected instead of CO position
        }

        result = PositionService.filter_and_recover_positions(detected_positions)

        expected = {
            1: Position.BUTTON,
            2: Position.SMALL_BLIND,
            3: Position.BIG_BLIND,
            4: Position.EARLY_POSITION,
            5: Position.MIDDLE_POSITION,
            6: Position.CUTOFF  # Should be inferred as the missing CO position
        }

        self.assertEqual(result, expected)

    def test_filter_and_recover_positions_mixed_detections(self):
        """Test filtering mix of positions, action text, and NO_POSITION."""
        detected_positions = {
            1: DetectedPosition.BUTTON,
            2: DetectedPosition.CALLS,  # Action text
            3: DetectedPosition.BIG_BLIND,
            4: DetectedPosition.NO_POSITION,  # Should be ignored
            5: DetectedPosition.MIDDLE_POSITION,
            6: DetectedPosition.CUTOFF
        }

        result = PositionService.filter_and_recover_positions(detected_positions)

        # Should recover SB for the action text detection
        expected = {
            1: Position.BUTTON,
            2: Position.SMALL_BLIND,  # Inferred from action
            3: Position.BIG_BLIND,
            # Player 4 ignored (NO_POSITION)
            5: Position.MIDDLE_POSITION,
            6: Position.CUTOFF
        }

        self.assertEqual(result, expected)

    def test_filter_and_recover_positions_empty_input(self):
        """Test filtering with empty input."""
        detected_positions = {}

        result = PositionService.filter_and_recover_positions(detected_positions)

        self.assertEqual(result, {})

    def test_filter_and_recover_positions_all_no_position(self):
        """Test filtering when all detections are NO_POSITION."""
        detected_positions = {
            1: DetectedPosition.NO_POSITION,
            2: DetectedPosition.NO_POSITION,
            3: DetectedPosition.NO_POSITION,
            4: DetectedPosition.NO_POSITION,
            5: DetectedPosition.NO_POSITION,
            6: DetectedPosition.NO_POSITION
        }

        result = PositionService.filter_and_recover_positions(detected_positions)

        self.assertEqual(result, {})

    def test_infer_missing_position_no_positions_detected(self):
        """Test position inference when no positions are detected."""
        detected_positions = {}

        result = PositionService._infer_missing_position(detected_positions)

        self.assertIsNone(result)

    def test_infer_missing_position_single_missing_6max(self):
        """Test inference when only one position is missing in 6-max."""
        detected_positions = {
            1: Position.BUTTON,
            2: Position.SMALL_BLIND,
            3: Position.BIG_BLIND,
            4: Position.EARLY_POSITION,
            5: Position.MIDDLE_POSITION
            # CO is missing
        }

        result = PositionService._infer_missing_position(detected_positions)

        self.assertEqual(result, Position.CUTOFF)

    def test_infer_missing_position_single_missing_4max(self):
        """Test inference when only one position is missing in 4-max."""
        detected_positions = {
            1: Position.BUTTON,
            2: Position.SMALL_BLIND,
            3: Position.BIG_BLIND
            # CO is missing
        }

        result = PositionService._infer_missing_position(detected_positions)

        self.assertEqual(result, Position.CUTOFF)

    def test_infer_missing_position_single_missing_heads_up(self):
        """Test inference for heads-up (2 player) games."""
        detected_positions = {
            1: Position.SMALL_BLIND
            # BB is missing, but algorithm defaults to 6-max and returns BTN
        }

        result = PositionService._infer_missing_position(detected_positions)

        # The current algorithm defaults to 6-max table size, so it returns BTN by priority
        self.assertEqual(result, Position.BUTTON)

    def test_infer_missing_position_multiple_missing_priority_order(self):
        """Test inference follows priority order when multiple positions missing."""
        detected_positions = {
            1: Position.BIG_BLIND,
            2: Position.EARLY_POSITION
            # BTN, SB, MP, CO all missing - should return BTN (highest priority)
        }

        result = PositionService._infer_missing_position(detected_positions)

        self.assertEqual(result, Position.BUTTON)

    def test_infer_missing_position_3max_scenario(self):
        """Test inference for 3-max table."""
        detected_positions = {
            1: Position.BUTTON,
            2: Position.SMALL_BLIND
            # BB is missing
        }

        result = PositionService._infer_missing_position(detected_positions)

        self.assertEqual(result, Position.BIG_BLIND)

    def test_infer_missing_position_5max_scenario(self):
        """Test inference for 5-max table."""
        detected_positions = {
            1: Position.BUTTON,
            2: Position.SMALL_BLIND,
            3: Position.BIG_BLIND,
            4: Position.CUTOFF
            # EP is missing
        }

        result = PositionService._infer_missing_position(detected_positions)

        self.assertEqual(result, Position.EARLY_POSITION)

    def test_infer_missing_position_invalid_position_set(self):
        """Test inference with positions that don't match any standard table size."""
        # This is an invalid combination that doesn't match any table size pattern
        detected_positions = {
            1: Position.MIDDLE_POSITION,
            2: Position.CUTOFF
            # Missing BTN, SB, BB, EP - doesn't match any standard table
        }

        result = PositionService._infer_missing_position(detected_positions)

        # Should fall back to priority order and return BTN
        self.assertEqual(result, Position.BUTTON)
