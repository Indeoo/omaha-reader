import numpy as np
from loguru import logger
from matplotlib import pyplot as plt

from src.core.service.moves_by_street import group_moves_by_street
from src.core.utils.detect_utils import DetectUtils
from src.core.utils.drawing_utils import draw_all_detections, DetectionGroup, DetectionType, _flatten_action_lists


def get_street_actions(image: np.ndarray):
    actions = DetectUtils.get_player_actions_detection(image)
    positions = DetectUtils.detect_positions(image)

    result_image = draw_all_detections(
        image,
        [
            DetectionGroup(DetectionType.ACTIONS, _flatten_action_lists(actions))
        ]
    )
    plt.imshow(result_image)
    plt.show()

    detection_dict = convert_detection_to_dict(actions, positions)

    logger.info("Fixed")
    print(detection_dict)

    return group_moves_by_street(detection_dict)


def convert_detection_to_dict(actions, positions):
    result = {}

    for player_id, detection_list in actions.items():
        if player_id in positions:
            position_name = positions[player_id].position_name
            print(position_name)
            position_name = position_name[:-5] if position_name.endswith('_fold') or position_name.endswith(
                '_low') else position_name
            result[position_name] = [d.name for d in detection_list]

    return result
