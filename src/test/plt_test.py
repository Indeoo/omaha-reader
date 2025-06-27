import unittest

import cv2
from matplotlib import pyplot as plt


class PltTest(unittest.TestCase):

    def test_image_section(self):
        # Load and preprocess image
        img_path = f"src/test/tables/move_test.png"
        #img = cv2.imread(f"Dropbox/data_screenshots/_20250610_023049/_20250610_025342/02_unknown__2_50__5_Pot_Limit_Omaha.png")

        img = cv2.imread(img_path)
        # Convert BGR to RGB for display
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Print image shape for reference
        print("Image shape (h, w, c):", img.shape)

        # Initial guess for bubble ROI (tweak these values as needed)
        x, y, w, h = 310, 460, 50, 30
        roi = img_rgb[y:y + h, x:x + w]

        # Draw rectangle on the original image for context
        img_with_rect = img_rgb.copy()
        cv2.rectangle(img_with_rect, (x, y), (x + w, y + h), (255, 0, 0), 2)

        # Display the original with rectangle and the cropped ROI
        fig, axes = plt.subplots(1, 2, figsize=(10, 5))
        axes[0].imshow(img_with_rect)
        axes[0].set_title("Original with ROI")
        axes[0].axis("off")

        axes[1].imshow(roi)
        axes[1].set_title("Cropped Bubble")
        axes[1].axis("off")

        plt.show()