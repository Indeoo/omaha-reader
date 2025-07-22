import unittest

import cv2

from src.core.service.action_service import get_player_actions


class TestActionService(unittest.TestCase):

    def test_action_service(self):
        img_path = f"src/test/resources/bids/9_bid.png"
        img = cv2.imread(img_path)

        project_root = "/Users/indeoo/Project/OmahaSolver/TableScrapper"

        player_actions = get_player_actions(img, project_root)

        print(player_actions)
