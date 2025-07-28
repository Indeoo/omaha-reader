import unittest

import cv2

from src.core.service.action_service import get_street_actions


class TestActionDetectionService(unittest.TestCase):

    def test_action_detection_service(self):
        img_path = f"src/test/resources/bids/5_move.png"
        img = cv2.imread(img_path)

        player_actions = get_street_actions(img)

        print(player_actions)
