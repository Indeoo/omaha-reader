from typing import Dict, Optional

from loguru import logger

from shared.domain.detected_position import DetectedPosition
from shared.domain.detection import Detection
from shared.domain.position import Position


class PositionService:

    @staticmethod
    def get_positions(position_detections: dict[int, Detection]) -> dict[int, Position]:
        if len(position_detections.items()) < 6:
            raise Exception(f"Could not convert {position_detections.items()}")

        detected_positions = PositionService.convert_detections_to_detected_positions(position_detections)
        recovered_positions = PositionService.filter_and_recover_positions(detected_positions)

        return recovered_positions

    @staticmethod
    def convert_detections_to_detected_positions(positions: Dict[int, Detection]) -> Dict[int, DetectedPosition]:
        """
        Convert a dictionary of Detection objects to DetectedPosition enums.

        Args:
            positions: Dict mapping player_id to Detection objects

        Returns:
            Dict mapping player_id to DetectedPosition enums
        """
        converted_positions = {}

        for player_id, position_detection in positions.items():
            try:
                detected_position = DetectedPosition.from_detection_name(position_detection.name)
                converted_positions[player_id] = detected_position
            except ValueError as e:
                logger.warning(f"Skipping unknown detection '{position_detection.name}' for player {player_id}: {e}")
                continue

        return converted_positions

    @staticmethod
    def filter_and_recover_positions(detected_positions: Dict[int, DetectedPosition]) -> Dict[int, Position]:
        """
        Filter DetectedPosition enums to valid positions and recover missing positions
        from action evidence in a single pass.

        Args:
            detected_positions: Dict mapping player_id to DetectedPosition enums
        Returns:
            Dict mapping player_id to Position enums (direct positions + recovered positions)
        """
        result_positions = {}

        # Single pass: filter valid positions and recover from actions
        for player_id, detected_pos in detected_positions.items():
            if detected_pos.is_position():
                # Direct position conversion
                position_enum = detected_pos.to_position()
                if position_enum:
                    result_positions[player_id] = position_enum
                    logger.debug(f"Direct position for player {player_id}: {position_enum}")

            elif detected_pos.is_action():
                # Recover position for action text detected in position templates
                inferred_position_enum = PositionService._infer_missing_position(result_positions)

                if inferred_position_enum:
                    result_positions[player_id] = inferred_position_enum
                    logger.info(
                        f"Recovered position for player {player_id}: {inferred_position_enum} (detected action: {detected_pos.value})")

            # NO_POSITION is automatically ignored (neither is_position() nor is_action())

        return result_positions

    @staticmethod
    def _infer_missing_position(detected_positions: Dict[int, Position]) -> Optional[Position]:
        if not detected_positions:
            return None

        # Work directly with Position enums
        detected_position_enums = set(detected_positions.values())

        # Define position sets for different table sizes using Position enums
        position_table = Position.get_all_position_table()

        # Determine likely table size based on detected positions
        table_size = 6  # Default
        for size, positions in position_table.items():
            if detected_position_enums.issubset(positions):
                table_size = size
                break

        # Find missing positions for this table size
        expected_positions = position_table[table_size]
        missing_positions = expected_positions - detected_position_enums

        # Simple heuristic: if only one position is missing, assign it
        if len(missing_positions) == 1:
            return list(missing_positions)[0]

        # Use Position enum's action order for logical priority
        # Priority: most important positions first (Button, Blinds, then others)
        priority_order = [
            Position.BUTTON,      # Most important - dealer position
            Position.SMALL_BLIND, # Critical blind position
            Position.BIG_BLIND,   # Critical blind position
            Position.CUTOFF,      # Strong late position
            Position.EARLY_POSITION, # Early position
            Position.MIDDLE_POSITION # Least critical if present
        ]
        
        for position in priority_order:
            if position in missing_positions:
                return position

        return None