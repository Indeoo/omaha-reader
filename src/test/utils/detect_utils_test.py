import unittest

import cv2
from matplotlib import pyplot as plt

from src.core.utils.detect_utils import DetectUtils
from src.core.utils.drawing_utils import draw_all_detections, DetectionGroup, DetectionType, _flatten_action_lists


class TestDetectUtils(unittest.TestCase):

    def test_detect_positions(self):
        img_path = f"src/test/resources/bids/5_move.png"
        img = cv2.imread(img_path)

        actions = DetectUtils.get_player_actions_detection(img)

        result_image = draw_all_detections(
            img,
            [
                DetectionGroup(DetectionType.ACTIONS, _flatten_action_lists(actions))
            ]
        )
        plt.imshow(result_image)
        plt.show()