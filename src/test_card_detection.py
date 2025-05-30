import os

import cv2
import numpy as np
from typing import List, Tuple, Dict


class PokerInterfaceCardDetector:
    def __init__(self,
                 card_area_range: Tuple[int, int] = (1500, 12000),
                 aspect_ratio_range: Tuple[float, float] = (0.7, 1.4),
                 min_card_width: int = 25,
                 min_card_height: int = 25):
        """
        Detector specifically for poker interface cards (like the 4 blue cards shown)
        """
        self.card_area_range = card_area_range
        self.aspect_ratio_range = aspect_ratio_range
        self.min_card_width = min_card_width
        self.min_card_height = min_card_height

    def preprocess_for_blue_cards(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Preprocess specifically for blue cards on red background
        """
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Define blue color range (adjust these values based on your cards)
        # Blue cards typically have hue around 100-130
        lower_blue = np.array([90, 50, 100])  # Lower HSV threshold
        upper_blue = np.array([130, 255, 255])  # Upper HSV threshold

        # Create mask for blue regions
        blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)

        # Clean up the mask
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        blue_mask = cv2.morphologyEx(blue_mask, cv2.MORPH_CLOSE, kernel)
        blue_mask = cv2.morphologyEx(blue_mask, cv2.MORPH_OPEN, kernel)

        # Also try edge detection on grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 40, 120, apertureSize=3)

        # Combine color and edge information
        combined = cv2.bitwise_or(blue_mask, edges)

        return blue_mask, combined

    def is_poker_card_contour(self, contour: np.ndarray, image_shape: Tuple[int, int]) -> bool:
        """
        Check if contour looks like a poker interface card
        """
        # Calculate area
        area = cv2.contourArea(contour)

        # Check area range
        if not (self.card_area_range[0] <= area <= self.card_area_range[1]):
            return False

        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(contour)

        # Size validation
        if w < self.min_card_width or h < self.min_card_height:
            return False

        # Aspect ratio check (poker cards can be square-ish in interfaces)
        aspect_ratio = w / h if h > 0 else 0
        if not (self.aspect_ratio_range[0] <= aspect_ratio <= self.aspect_ratio_range[1]):
            return False

        # Solidity check (should be fairly filled)
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        if hull_area > 0:
            solidity = area / hull_area
            if solidity < 0.7:
                return False

        # Rectangle approximation
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        if len(approx) < 4 or len(approx) > 8:
            return False

        # Remove border margin check since cards might be anywhere
        # Don't filter by position - cards can be in center of interface

        return True

    def detect_poker_cards(self, image: np.ndarray) -> List[Dict]:
        """
        Detect poker cards in the interface
        """
        # Get both color mask and combined preprocessing
        blue_mask, combined = self.preprocess_for_blue_cards(image)

        # Find contours in combined image
        contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        cards = []

        for contour in contours:
            if self.is_poker_card_contour(contour, image.shape[:2]):
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)

                # Additional validation: check if this region is actually blue
                roi_mask = blue_mask[y:y + h, x:x + w]
                blue_pixels = cv2.countNonZero(roi_mask)
                total_pixels = w * h
                blue_ratio = blue_pixels / total_pixels if total_pixels > 0 else 0

                # Only accept if a reasonable portion is blue
                if blue_ratio > 0.3:  # At least 30% blue pixels
                    # Get rotated rectangle
                    rect = cv2.minAreaRect(contour)
                    box = cv2.boxPoints(rect)
                    box = np.array(box, dtype=np.int32)

                    card_info = {
                        'contour': contour,
                        'bounding_rect': (x, y, w, h),
                        'rotated_rect': rect,
                        'box_points': box,
                        'area': cv2.contourArea(contour),
                        'center': (int(rect[0][0]), int(rect[0][1])),
                        'width': w,
                        'height': h,
                        'aspect_ratio': w / h if h > 0 else 0,
                        'blue_ratio': blue_ratio
                    }

                    cards.append(card_info)

        # Sort cards left to right (for the 4 cards in a row)
        cards.sort(key=lambda card: card['center'][0])

        return cards

    def detect_cards_alternative_method(self, image: np.ndarray) -> List[Dict]:
        """
        Alternative detection method using template matching approach
        """
        # Convert to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Create a more aggressive blue mask
        lower_blue1 = np.array([100, 100, 100])
        upper_blue1 = np.array([130, 255, 255])
        mask1 = cv2.inRange(hsv, lower_blue1, upper_blue1)

        # Second blue range for different lighting
        lower_blue2 = np.array([90, 80, 80])
        upper_blue2 = np.array([140, 255, 255])
        mask2 = cv2.inRange(hsv, lower_blue2, upper_blue2)

        # Combine masks
        blue_mask = cv2.bitwise_or(mask1, mask2)

        # Morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        blue_mask = cv2.morphologyEx(blue_mask, cv2.MORPH_CLOSE, kernel)
        blue_mask = cv2.morphologyEx(blue_mask, cv2.MORPH_OPEN, kernel)

        # Find contours
        contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        cards = []

        for contour in contours:
            area = cv2.contourArea(contour)
            if 1000 < area < 15000:  # Broader area range
                x, y, w, h = cv2.boundingRect(contour)

                # Basic size and aspect ratio checks
                if w > 20 and h > 20:
                    aspect_ratio = w / h
                    if 0.5 < aspect_ratio < 2.0:  # Very broad aspect ratio
                        rect = cv2.minAreaRect(contour)
                        box = cv2.boxPoints(rect)
                        box = np.array(box, dtype=np.int32)

                        card_info = {
                            'contour': contour,
                            'bounding_rect': (x, y, w, h),
                            'rotated_rect': rect,
                            'box_points': box,
                            'area': area,
                            'center': (int(rect[0][0]), int(rect[0][1])),
                            'width': w,
                            'height': h,
                            'aspect_ratio': aspect_ratio,
                            'method': 'alternative'
                        }

                        cards.append(card_info)

        # Sort by position
        cards.sort(key=lambda card: card['center'][0])

        return cards

    def draw_detected_cards(self, image: np.ndarray, cards: List[Dict]) -> np.ndarray:
        """
        Draw detected cards with detailed information
        """
        result = image.copy()

        for i, card in enumerate(cards):
            # Draw contour in green
            cv2.drawContours(result, [card['box_points']], -1, (0, 255, 0), 2)

            # Draw bounding rectangle in yellow
            x, y, w, h = card['bounding_rect']
            cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 255), 1)

            # Add labels
            label = f'Card {i + 1}'
            cv2.putText(result, label, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Add area and ratio info
            info = f'A:{int(card["area"])}'
            cv2.putText(result, info, (x, y + h + 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)

            # Add center point
            center = card['center']
            cv2.circle(result, center, 3, (255, 0, 255), -1)

        return result

    def show_debug_images(self, image: np.ndarray):
        """
        Show debug images to help tune parameters
        """
        blue_mask, combined = self.preprocess_for_blue_cards(image)

        # Try alternative method too
        cards_method1 = self.detect_poker_cards(image)
        cards_method2 = self.detect_cards_alternative_method(image)

        print(f"Method 1 detected: {len(cards_method1)} cards")
        print(f"Method 2 detected: {len(cards_method2)} cards")

        # Draw results
        result1 = self.draw_detected_cards(image, cards_method1)
        result2 = self.draw_detected_cards(image, cards_method2)

        return {
            'original': image,
            'blue_mask': blue_mask,
            'combined_edges': combined,
            'method1_result': result1,
            'method2_result': result2,
            'cards_method1': cards_method1,
            'cards_method2': cards_method2
        }


def test_poker_interface_detection(image_path: str = None):
    """
    Test the poker interface card detection
    """
    detector = PokerInterfaceCardDetector(
        card_area_range=(1000, 10000),  # Adjust based on actual card sizes
        aspect_ratio_range=(0.6, 1.5),  # Allow for square-ish cards
        min_card_width=20,
        min_card_height=20
    )

    if image_path:
        image = cv2.imread(image_path)
        if image is None:
            print(f"Could not load image: {image_path}")
            return
    else:
        # Create test image with blue rectangles
        image = np.ones((400, 600, 3), dtype=np.uint8) * 50  # Dark red background
        image[:, :] = [50, 50, 150]  # Red background

        # Add 4 blue cards
        cards_x = [150, 220, 290, 360]
        for i, x in enumerate(cards_x):
            cv2.rectangle(image, (x, 100), (x + 50, 150), (200, 100, 50), -1)  # Blue card
            cv2.putText(image, str(i + 1), (x + 20, 130),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # Test detection
    debug_results = detector.show_debug_images(image)

    return debug_results


def save_detected_cards(debug_results, original_image):
    """
    Simple function to save detected cards to detected_cards/ folder
    """
    # Create folder
    os.makedirs("../detected_cards", exist_ok=True)

    # Get detected cards from method 1 (primary method)
    detected_cards = debug_results['cards_method1']

    # Save each card as individual image
    for i, card in enumerate(detected_cards):
        x, y, w, h = card['bounding_rect']
        card_image = original_image[y:y + h, x:x + w]
        cv2.imwrite(f"detected_cards/card_{i + 1}.png", card_image)

    print(f"Saved {len(detected_cards)} cards to detected_cards/ folder")
    return len(detected_cards)


if __name__ == "__main__":
    # Test with your poker image
    results = test_poker_interface_detection("../screenshots/img.png")

    # Load the original image for saving cards
    image = cv2.imread("../screenshots/img.png")

    # Save detected cards
    save_detected_cards(results, image)