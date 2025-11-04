import os
import unittest

import cv2
from matplotlib import pyplot as plt

from table_detector.utils.detect_utils import DetectUtils
from table_detector.utils.drawing_utils import draw_all_detections, DetectionGroup, DetectionType, _flatten_action_lists


class TestDetectUtils(unittest.TestCase):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up 4 levels: utils -> test -> table_detector -> apps -> project_root
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..'))
    # Use correct path: apps/table_detector/test/resources/detection/action
    action_folder = os.path.join(project_root, "apps", "table_detector", "test", "resources", "detection", "action")

    def test_detect_player_actions_1(self):
        img_path = os.path.join(self.action_folder, "1.png")
        img = cv2.imread(img_path)

        actions = DetectUtils.get_player_actions_detection(img)

        result_image = draw_all_detections(
            img,
            [
                DetectionGroup(DetectionType.ACTIONS, _flatten_action_lists(actions))
            ],
            show_search_regions=True
        )
        result_image_rgb = cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB)
        height, width = result_image_rgb.shape[:2]
        plt.figure(figsize=(width/100, height/100), dpi=100)
        plt.imshow(result_image_rgb)
        plt.axis('off')
        plt.tight_layout(pad=0)
        plt.show()

    def test_detect_player_actions_2(self):
        img_path = os.path.join(self.action_folder, "2.png")
        img = cv2.imread(img_path)

        actions = DetectUtils.get_player_actions_detection(img)

        result_image = draw_all_detections(
            img,
            [
                DetectionGroup(DetectionType.ACTIONS, _flatten_action_lists(actions))
            ]
        )
        result_image_rgb = cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB)
        height, width = result_image_rgb.shape[:2]
        plt.figure(figsize=(width/100, height/100), dpi=100)
        plt.imshow(result_image_rgb)
        plt.axis('off')
        plt.tight_layout(pad=0)
        plt.show()

    def test_detect_player_actions_3(self):
        img_path = os.path.join(self.action_folder, "3.png")
        img = cv2.imread(img_path)

        actions = DetectUtils.get_player_actions_detection(img)

        result_image = draw_all_detections(
            img,
            [
                DetectionGroup(DetectionType.ACTIONS, _flatten_action_lists(actions))
            ]
        )
        result_image_rgb = cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB)
        height, width = result_image_rgb.shape[:2]
        plt.figure(figsize=(width/100, height/100), dpi=100)
        plt.imshow(result_image_rgb)
        plt.axis('off')
        plt.tight_layout(pad=0)
        plt.show()

    def test_detect_player_actions_4(self):
        img_path = os.path.join(self.action_folder, "4.png")
        img = cv2.imread(img_path)

        actions = DetectUtils.get_player_actions_detection(img)

        result_image = draw_all_detections(
            img,
            [
                DetectionGroup(DetectionType.ACTIONS, _flatten_action_lists(actions))
            ]
        )
        result_image_rgb = cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB)
        height, width = result_image_rgb.shape[:2]
        plt.figure(figsize=(width/100, height/100), dpi=100)
        plt.imshow(result_image_rgb)
        plt.axis('off')
        plt.tight_layout(pad=0)
        plt.show()

    def test_detect_player_actions_5(self):
        img_path = os.path.join(self.action_folder, "5.png")
        img = cv2.imread(img_path)

        actions = DetectUtils.get_player_actions_detection(img)

        result_image = draw_all_detections(
            img,
            [
                DetectionGroup(DetectionType.ACTIONS, _flatten_action_lists(actions))
            ]
        )
        result_image_rgb = cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB)
        height, width = result_image_rgb.shape[:2]
        plt.figure(figsize=(width/100, height/100), dpi=100)
        plt.imshow(result_image_rgb)
        plt.axis('off')
        plt.tight_layout(pad=0)
        plt.show()

    def test_detect_player_actions_6(self):
        img_path = os.path.join(self.action_folder, "6.png")
        img = cv2.imread(img_path)

        actions = DetectUtils.get_player_actions_detection(img)

        result_image = draw_all_detections(
            img,
            [
                DetectionGroup(DetectionType.ACTIONS, _flatten_action_lists(actions))
            ]
        )
        result_image_rgb = cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB)
        height, width = result_image_rgb.shape[:2]
        plt.figure(figsize=(width/100, height/100), dpi=100)
        plt.imshow(result_image_rgb)
        plt.axis('off')
        plt.tight_layout(pad=0)
        plt.show()

    def test_detect_player_actions_7(self):
        img_path = os.path.join(self.action_folder, "7.png")
        img = cv2.imread(img_path)

        actions = DetectUtils.get_player_actions_detection(img)

        result_image = draw_all_detections(
            img,
            [
                DetectionGroup(DetectionType.ACTIONS, _flatten_action_lists(actions))
            ]
        )
        result_image_rgb = cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB)
        height, width = result_image_rgb.shape[:2]
        plt.figure(figsize=(width/100, height/100), dpi=100)
        plt.imshow(result_image_rgb)
        plt.axis('off')
        plt.tight_layout(pad=0)
        plt.show()