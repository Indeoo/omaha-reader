import cv2
import numpy as np


class ImagePreprocessor:

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess the image for better card detection
        Focus on detecting the rounded rectangle borders
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)

        # Use Canny edge detection to find the card borders
        edges = cv2.Canny(blurred, 50, 150, apertureSize=3)

        # Apply morphological operations to connect edges and fill gaps
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        edges = cv2.dilate(edges, kernel, iterations=1)

        return edges