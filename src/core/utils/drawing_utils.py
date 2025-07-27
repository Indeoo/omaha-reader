from typing import List, Dict, Tuple
from enum import Enum
import cv2
import numpy as np
from loguru import logger

from src.core.domain.captured_window import CapturedWindow
from src.core.domain.detected_bid import DetectedBid
from src.core.domain.game_snapshot import GameSnapshot
from src.core.domain.detection import Detection
from src.core.utils.opencv_utils import save_opencv_image


class DetectionType(Enum):
    """Enum for different types of detections with their display properties."""
    PLAYER_CARDS = ("player_cards", (0, 255, 0), True)  # Green, show scale
    TABLE_CARDS = ("table_cards", (0, 0, 255), True)   # Red, show scale
    POSITIONS = ("positions", (0, 255, 255), False)     # Yellow, no scale
    BIDS = ("bids", (255, 0, 255), False)               # Magenta, no scale
    ACTIONS = ("actions", (255, 165, 0), False)         # Orange, no scale
    
    def __init__(self, name: str, color: Tuple[int, int, int], show_scale: bool):
        self.type_name = name
        self.color = color
        self.show_scale = show_scale


class DetectionGroup:
    """Represents a group of detections of the same type."""
    def __init__(self, detection_type: DetectionType, detections: List[Detection]):
        self.detection_type = detection_type
        self.detections = detections
        
    def __len__(self) -> int:
        return len(self.detections)
        
    def __bool__(self) -> bool:
        return bool(self.detections)


def save_detection_result(timestamp_folder: str, captured_image: CapturedWindow, game_snapshot: GameSnapshot):
    window_name = captured_image.window_name
    filename = captured_image.filename

    try:
        cv2_image = captured_image.get_cv2_image()
        
        # Gather all detections into groups
        detection_groups = _gather_all_detections(game_snapshot)
        
        # Draw all detections using universal method
        result_image = draw_all_detections(cv2_image, detection_groups)
        
        # Save result image
        result_filename = filename.replace('.png', '_result.png')
        save_opencv_image(result_image, timestamp_folder, result_filename)
        
        # Log summary
        _log_detection_summary(result_filename, detection_groups)

    except Exception as e:
        logger.error(f"    ❌ Error saving result image for {window_name}: {str(e)}")
        raise e


def draw_all_detections(image: np.ndarray, detection_groups: List[DetectionGroup]) -> np.ndarray:
    result = image.copy()
    
    for group in detection_groups:
        if group.detections:  # Only draw if there are detections
            result = _draw_detection_group(result, group)
            
    return result


def _draw_detection_group(
        image: np.ndarray,
        group: DetectionGroup,
        thickness: int = 2,
        font_scale: float = 0.6
) -> np.ndarray:
    result = image.copy()
    color = group.detection_type.color
    
    for detection in group.detections:
        # Draw bounding rectangle
        x, y, w, h = detection.bounding_rect
        cv2.rectangle(result, (x, y), (x + w, y + h), color, thickness)
        
        # Draw center point
        cv2.circle(result, detection.center, 5, (255, 0, 0), -1)
        
        # Draw detection label with score
        label = f"{detection.name} ({detection.match_score:.2f})"
        cv2.putText(result, label, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)
        
        # Draw scale information if applicable
        if group.detection_type.show_scale and hasattr(detection, 'scale'):
            scale_label = f"Scale: {detection.scale:.1f}"
            cv2.putText(result, scale_label, (x, y + h + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale * 0.7, (255, 255, 0), 1)
    
    return result


def _convert_bids_to_detections(detected_bids: Dict[int, DetectedBid]) -> List[Detection]:
    detections = []

    for bid in detected_bids.values():
        detection = Detection(
            name=f"P{bid.position}: ${bid.amount_text}",
            center=bid.center,
            bounding_rect=bid.bounding_rect,
            match_score=1.0
        )
        detections.append(detection)
    return detections


def _flatten_action_lists(user_actions: Dict[int, List[Detection]]) -> List[Detection]:
    detections = []
    for action_list in user_actions.values():
        detections.extend(action_list)
    return detections

def _gather_all_detections(game_snapshot: GameSnapshot) -> List[DetectionGroup]:
    detection_groups = []
    
    # Player cards
    if game_snapshot.player_cards:
        detection_groups.append(
            DetectionGroup(DetectionType.PLAYER_CARDS, game_snapshot.player_cards)
        )
    
    # Table cards
    if game_snapshot.table_cards:
        detection_groups.append(
            DetectionGroup(DetectionType.TABLE_CARDS, game_snapshot.table_cards)
        )
    
    # Positions
    if game_snapshot.positions:
        position_detections = list(game_snapshot.positions.values())
        detection_groups.append(
            DetectionGroup(DetectionType.POSITIONS, position_detections)
        )
    
    # Bids (convert to detections first)
    if game_snapshot.bids:
        bid_detections = _convert_bids_to_detections(game_snapshot.bids)
        detection_groups.append(
            DetectionGroup(DetectionType.BIDS, bid_detections)
        )
    
    # Actions (flatten action lists)
    if game_snapshot.actions:
        action_detections = _flatten_action_lists(game_snapshot.actions)
        detection_groups.append(
            DetectionGroup(DetectionType.ACTIONS, action_detections)
        )
    
    return detection_groups


def _log_detection_summary(filename: str, detection_groups: List[DetectionGroup]) -> None:
    if detection_groups:
        drawn_items = [
            f"{len(group)} {group.detection_type.type_name}" 
            for group in detection_groups if group
        ]
        if drawn_items:
            logger.info(f"    📷 Saved {filename} with: {', '.join(drawn_items)}")
        else:
            logger.info(f"    📷 Saved {filename} (no detections)")
    else:
        logger.info(f"    📷 Saved {filename} (no detections)")
