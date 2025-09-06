import unittest

from table_detector.test.service.test_utils import load_image
from table_detector.utils.detect_utils import DetectUtils


class TestDetectUtils(unittest.TestCase):

    def test_detect_cb_position(self):
        cv2_image = load_image("7.png")

        detections = DetectUtils.get_player_actions_detection(cv2_image)[1]

        self.assertEqual(
            detections[0].name,
            'or_2'
        )

        self.assertEqual(
            detections[1].name,
            'cb'
        )

    def test_detect_l_position(self):
        cv2_image = load_image("8.png")

        detections = DetectUtils.get_player_actions_detection(cv2_image)[1]

        print(detections)