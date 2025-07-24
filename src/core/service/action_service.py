import numpy as np

from src.core.service.moves_by_street import group_moves_by_street
from src.core.utils.detect_utils import DetectUtils


def get_street_actions(image: np.ndarray):
    actions = DetectUtils.get_player_actions_detection(image)

    detection_dict = convert_detection_to_dict(actions)

    return group_moves_by_street(detection_dict)


def convert_detection_to_dict(actions):
    return {player_id: [d.name for d in detection] for player_id, detection in actions.items()}
