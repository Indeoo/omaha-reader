import cv2
import numpy as np
from typing import List, Tuple, Dict

class HandCardDetector:
    def __init__(self,
                 hand_card_area_range: Tuple[int, int] = (1000, 8000),
                 aspect_ratio_range: Tuple[float, float] = (0.6, 0.8),
                 min_card_width: int = 20,
                 min_card_height: int = 30):
        """
        Initialize the hand card detector - specialized for smaller cards

        Args:
            hand_card_area_range: Min and max area for hand cards (smaller range)
            aspect_ratio_range: Expected aspect ratio range for cards (width/height)
            min_card_width: Minimum width in pixels for a valid card
            min_card_height: Minimum height in pixels for a valid card
        """
        self.hand_card_area_range = hand_card_area_range
        self.aspect_ratio_range = aspect_ratio_range
        self.min_card_width = min_card_width
        self.min_card_height = min_card_height

    def preprocess_image_for_hands(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess the image specifically for hand card detection
        More sensitive edge detection for smaller cards
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply slight Gaussian blur to reduce noise but preserve small details
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)

        # Use more sensitive Canny edge detection for small cards
        edges = cv2.Canny(blurred, 30, 100, apertureSize=3)

        # Lighter morphological operations to preserve small card details
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        edges = cv2.dilate(edges, kernel, iterations=1)

        return edges

    def is_hand_card_contour(self, contour: np.ndarray, image_shape: Tuple[int, int]) -> bool:
        """
        Check if a contour looks like a hand card (smaller, specific properties)
        """
        # Calculate area
        area = cv2.contourArea(contour)

        # Check if area is in hand card range
        if not (self.hand_card_area_range[0] <= area <= self.hand_card_area_range[1]):
            return False

        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(contour)

        # Filter out very small contours
        if w < self.min_card_width or h < self.min_card_height:
            return False

        # Check aspect ratio - hand cards are typically more rectangular
        aspect_ratio = w / h if h > 0 else 0

        # Allow for both orientations (portrait and landscape)
        valid_aspect = (self.aspect_ratio_range[0] <= aspect_ratio <= self.aspect_ratio_range[1]) or \
                       (1 / self.aspect_ratio_range[1] <= aspect_ratio <= 1 / self.aspect_ratio_range[0])

        if not valid_aspect:
            return False

        # Check if contour is reasonably filled (not just an outline)
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        if hull_area > 0:
            solidity = area / hull_area
            if solidity < 0.6:  # Allow for rounded corners and smaller cards
                return False

        # Check contour approximation - should be roughly rectangular
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        # Hand cards should approximate to 4-6 points (allowing for rounded corners)
        if not (4 <= len(approx) <= 8):
            return False

        # Additional check: reject contours that are too close to image borders
        # (might be partial cards or UI elements)
        border_margin = 10
        if (x < border_margin or y < border_margin or
                x + w > image_shape[1] - border_margin or
                y + h > image_shape[0] - border_margin):
            return False

        return True

    def detect_hand_cards(self, image: np.ndarray) -> List[Dict]:
        """
        Detect hand cards in the image

        Returns:
            List of dictionaries containing hand card information
        """
        # Preprocess image for hand card detection
        processed = self.preprocess_image_for_hands(image)

        # Find contours
        contours, _ = cv2.findContours(processed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        hand_cards = []

        for contour in contours:
            if self.is_hand_card_contour(contour, image.shape[:2]):
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)

                # Get rotated rectangle for better representation
                rect = cv2.minAreaRect(contour)
                box = cv2.boxPoints(rect)
                box = np.array(box, dtype=np.int32)

                # Calculate additional properties
                area = cv2.contourArea(contour)
                perimeter = cv2.arcLength(contour, True)

                card_info = {
                    'contour': contour,
                    'bounding_rect': (x, y, w, h),
                    'rotated_rect': rect,
                    'box_points': box,
                    'area': area,
                    'perimeter': perimeter,
                    'center': (int(rect[0][0]), int(rect[0][1])),
                    'width': w,
                    'height': h,
                    'aspect_ratio': w / h if h > 0 else 0
                }

                hand_cards.append(card_info)

        # Sort cards by position (left to right, top to bottom)
        hand_cards.sort(key=lambda card: (card['center'][1], card['center'][0]))

        return hand_cards

    def draw_detected_hand_cards(self, image: np.ndarray, hand_cards: List[Dict]) -> np.ndarray:
        """
        Draw detected hand cards on the image for visualization
        """
        result_image = image.copy()

        for i, card in enumerate(hand_cards):
            # Draw contour in green
            cv2.drawContours(result_image, [card['box_points']], -1, (0, 255, 0), 2)

            # Draw bounding rectangle in blue
            x, y, w, h = card['bounding_rect']
            cv2.rectangle(result_image, (x, y), (x + w, y + h), (255, 0, 0), 1)

            # Add label with card number
            label = f'Hand {i + 1}'
            cv2.putText(result_image, label, (card['center'][0] - 20, card['center'][1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Add area info
            area_text = f'{int(card["area"])}'
            cv2.putText(result_image, area_text, (card['center'][0] - 15, card['center'][1] + 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)

        return result_image

    def extract_hand_card_region(self, image: np.ndarray, card_info: Dict) -> np.ndarray:
        """
        Extract and straighten a hand card region from the image
        """
        # Get the rotated rectangle points
        rect = card_info['rotated_rect']
        box = card_info['box_points']

        # Get width and height of the rotated rectangle
        width = int(rect[1][0])
        height = int(rect[1][1])

        # Ensure we have positive dimensions
        if width <= 0 or height <= 0:
            x, y, w, h = card_info['bounding_rect']
            return image[y:y + h, x:x + w]

        # Define destination points for perspective transform
        dst_pts = np.array([
            [0, height - 1],
            [0, 0],
            [width - 1, 0],
            [width - 1, height - 1]
        ], dtype="float32")

        # Get perspective transform matrix
        src_pts = box.astype("float32")
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)

        # Apply perspective transform
        warped = cv2.warpPerspective(image, M, (width, height))

        return warped

    def filter_by_position(self, hand_cards: List[Dict], region: str = 'bottom') -> List[Dict]:
        """
        Filter hand cards by their position in the image

        Args:
            hand_cards: List of detected hand cards
            region: 'bottom', 'top', 'left', 'right' - where to look for hand cards

        Returns:
            Filtered list of hand cards
        """
        if not hand_cards:
            return []

        if region == 'bottom':
            # Get cards in bottom third of image
            max_y = max(card['center'][1] for card in hand_cards)
            threshold_y = max_y * 0.7
            return [card for card in hand_cards if card['center'][1] >= threshold_y]

        elif region == 'top':
            # Get cards in top third of image
            min_y = min(card['center'][1] for card in hand_cards)
            threshold_y = min_y + (max(card['center'][1] for card in hand_cards) - min_y) * 0.3
            return [card for card in hand_cards if card['center'][1] <= threshold_y]

        # Add more position filters as needed
        return hand_cards
