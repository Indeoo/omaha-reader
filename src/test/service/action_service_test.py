import unittest

import cv2

from src.core.service.action_service import get_street_actions
from src.core.utils.detect_utils import DetectUtils


class TestActionService(unittest.TestCase):

    def test_action_service(self):
        img_path = f"src/test/resources/bids/5_move.png"
        img = cv2.imread(img_path)

        player_actions = DetectUtils.get_player_actions_detection(img)

        print(player_actions)

    def test_get_street_actions(self):
        img_path = f"src/test/resources/actions/3_move_tern.png"
        img = cv2.imread(img_path)

        player_actions = get_street_actions(img)

        print(player_actions)
