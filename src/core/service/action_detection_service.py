from matplotlib import pyplot as plt

from src.core.utils.detect_utils import DetectUtils
from src.core.utils.drawing_utils import draw_all_detections, DetectionGroup, DetectionType, _flatten_action_lists


def detection_dict(image):
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

    return convert_detection_to_dict(actions, positions)


def convert_detection_to_dict(actions, positions):
    result = {}

    for player_id, detection_list in actions.items():
        if player_id in positions:
            position_name = positions[player_id].position_name
            print(position_name)
            if position_name.endswith('_fold'):
                position_name = position_name[:-5]  # Remove exactly "_fold"
            elif position_name.endswith('_low'):
                position_name = position_name[:-4]  # Remove exactly "_low"

            result[position_name] = [d.name for d in detection_list]

    return result