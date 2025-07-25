import numpy as np

from src.core.service.moves_by_street import group_moves_by_street
from src.core.utils.detect_utils import DetectUtils


def get_street_actions(image: np.ndarray):
    actions = DetectUtils.get_player_actions_detection(image)
    positions = DetectUtils.detect_positions(image)

    detection_dict = convert_detection_to_dict(actions, positions)

    detection_dict_unfolded = {k[:-5] if k.endswith('_fold') else k: v for k, v in
                      detection_dict.items()}

    detection_dict_unlowed = {k[:-5] if k.endswith('_low') else k: v for k, v in
                      detection_dict_unfolded.items()}

    return group_moves_by_street(detection_dict_unlowed)


def convert_detection_to_dict(actions, positions):
    result = {}

    for player_id, detection_list in actions.items():
        if player_id in positions:
            position_name = positions[player_id].position_name
            print(position_name)
            result[position_name] = [d.name for d in detection_list]

    return result