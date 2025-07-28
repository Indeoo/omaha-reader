import unittest

import cv2

from src.core.service.action_service import get_street_actions


class TestActionService(unittest.TestCase):

    def test_get_street_actions(self):
        img_path = f"src/test/resources/actions/3_move_tern.png"
        img = cv2.imread(img_path)

        player_actions = get_street_actions(img)

        print(player_actions)
