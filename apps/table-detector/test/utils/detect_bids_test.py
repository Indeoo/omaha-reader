import unittest

import cv2
from matplotlib import pyplot as plt

from apps.client.utils.bid_detect_utils import detect_bids
from apps.client.services.opencv_utils import draw_detected_bids


class TestDetectBids(unittest.TestCase):

    def test_detect_bids(self):
        img_path = f"src/test/resources/bids/9_bid.png"
        img = cv2.imread(img_path)

        bids = detect_bids(img)

        result_image = draw_detected_bids(img, bids)

        # Convert BGR to RGB for matplotlib display
        result_image_rgb = cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB)

        # Display with matplotlib
        plt.figure(figsize=(12, 8))
        plt.imshow(result_image_rgb)
        plt.title("Detected Bids")
        plt.axis('off')
        plt.show()
