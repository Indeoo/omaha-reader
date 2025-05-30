import cv2
import numpy as np
from typing import List, Tuple, Dict
import matplotlib.pyplot as plt


class PokerCardDetector:
    def __init__(self,
                 hand_card_area_range: Tuple[int, int] = (5000, 15000),
                 table_card_area_range: Tuple[int, int] = (15000, 50000),
                 aspect_ratio_range: Tuple[float, float] = (0.6, 0.8)):
        """
        Initialize the poker card detector

        Args:
            hand_card_area_range: Min and max area for hand cards
            table_card_area_range: Min and max area for table cards
            aspect_ratio_range: Expected aspect ratio range for cards (width/height)
        """
        self.hand_card_area_range = hand_card_area_range
        self.table_card_area_range = table_card_area_range
        self.aspect_ratio_range = aspect_ratio_range

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

    def is_card_like_contour(self, contour: np.ndarray, image_shape: Tuple[int, int]) -> bool:
        """
        Check if a contour looks like a card based on shape properties
        Updated for rounded rectangle card borders
        """
        # Calculate area
        area = cv2.contourArea(contour)

        # Check if area is in expected range for any card type
        min_area = min(self.hand_card_area_range[0], self.table_card_area_range[0])
        max_area = max(self.hand_card_area_range[1], self.table_card_area_range[1])

        if not (min_area <= area <= max_area):
            return False

        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(contour)

        # Filter out very small or very large contours relative to image size
        image_area = image_shape[0] * image_shape[1]
        if area < image_area * 0.001 or area > image_area * 0.3:
            return False

        # Check aspect ratio (cards are typically rectangular)
        aspect_ratio = w / h if h > 0 else 0

        # Allow for both orientations and be more flexible with rounded corners
        valid_aspect = (0.5 <= aspect_ratio <= 0.9) or (1.1 <= aspect_ratio <= 2.0)
        if not valid_aspect:
            return False

        # Check if contour is reasonably filled (not just an outline)
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        if hull_area > 0:
            solidity = area / hull_area
            if solidity < 0.7:  # Allow for rounded corners
                return False

        # Check if the contour has reasonable dimensions
        if w < 20 or h < 30:  # Too small to be a card
            return False

        return True

    def classify_card_type(self, contour: np.ndarray) -> str:
        """
        Classify if the detected card is a hand card or table card based on size
        """
        area = cv2.contourArea(contour)

        if self.hand_card_area_range[0] <= area <= self.hand_card_area_range[1]:
            return "hand"
        elif self.table_card_area_range[0] <= area <= self.table_card_area_range[1]:
            return "table"
        else:
            return "unknown"

    def detect_cards(self, image: np.ndarray) -> Dict[str, List[Dict]]:
        """
        Detect all cards in the image and classify them
        Updated for rounded rectangle card detection

        Returns:
            Dictionary with 'hand_cards' and 'table_cards' lists containing card info
        """
        # Preprocess image
        processed = self.preprocess_image(image)

        # Find contours
        contours, _ = cv2.findContours(processed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        hand_cards = []
        table_cards = []

        for contour in contours:
            if self.is_card_like_contour(contour, image.shape[:2]):
                card_type = self.classify_card_type(contour)

                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)

                # Get rotated rectangle for better representation
                rect = cv2.minAreaRect(contour)
                box = cv2.boxPoints(rect)
                box = np.array(box, dtype=np.int32)

                card_info = {
                    'contour': contour,
                    'bounding_rect': (x, y, w, h),
                    'rotated_rect': rect,
                    'box_points': box,
                    'area': cv2.contourArea(contour),
                    'center': (int(rect[0][0]), int(rect[0][1]))
                }

                if card_type == "hand":
                    hand_cards.append(card_info)
                elif card_type == "table":
                    table_cards.append(card_info)

        return {
            'hand_cards': hand_cards,
            'table_cards': table_cards
        }

    def draw_detected_cards(self, image: np.ndarray, detected_cards: Dict) -> np.ndarray:
        """
        Draw detected cards on the image for visualization
        """
        result_image = image.copy()

        # Draw hand cards in blue
        for card in detected_cards['hand_cards']:
            cv2.drawContours(result_image, [card['box_points']], -1, (255, 0, 0), 2)
            cv2.putText(result_image, 'Hand', card['center'],
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

        # Draw table cards in red
        for card in detected_cards['table_cards']:
            cv2.drawContours(result_image, [card['box_points']], -1, (0, 0, 255), 2)
            cv2.putText(result_image, 'Table', card['center'],
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        return result_image

    def extract_card_region(self, image: np.ndarray, card_info: Dict) -> np.ndarray:
        """
        Extract and straighten a card region from the image
        """
        # Get the rotated rectangle points
        rect = card_info['rotated_rect']
        box = card_info['box_points']

        # Get width and height of the rotated rectangle
        width = int(rect[1][0])
        height = int(rect[1][1])

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


# Example usage and testing functions
def test_card_detection(image_path: str = None):
    """
    Test the card detection system
    """
    # Adjust parameters based on your card images
    detector = PokerCardDetector(
        hand_card_area_range=(1000, 8000),  # Smaller cards
        table_card_area_range=(8000, 25000),  # Larger cards
        aspect_ratio_range=(0.5, 0.85)  # Typical card proportions
    )

    if image_path:
        # Load image from file
        image = cv2.imread(image_path)
        if image is None:
            print(f"Could not load image from {image_path}")
            return None, None
    else:
        # Create a sample image with rectangles for testing
        image = np.ones((600, 800, 3), dtype=np.uint8) * 50

        # Draw sample "cards" with white borders - hand cards (smaller)
        cv2.rectangle(image, (48, 48), (132, 182), (255, 255, 255), 2)  # Border
        cv2.rectangle(image, (50, 50), (130, 180), (200, 200, 200), -1)  # Card

        cv2.rectangle(image, (148, 48), (232, 182), (255, 255, 255), 2)  # Border
        cv2.rectangle(image, (150, 50), (230, 180), (200, 200, 200), -1)  # Card

        # Draw sample "cards" - table cards (larger)
        cv2.rectangle(image, (298, 98), (422, 222), (255, 255, 255), 2)  # Border
        cv2.rectangle(image, (300, 100), (420, 220), (200, 200, 200), -1)  # Card

        cv2.rectangle(image, (448, 98), (572, 222), (255, 255, 255), 2)  # Border
        cv2.rectangle(image, (450, 100), (570, 220), (200, 200, 200), -1)  # Card

        cv2.rectangle(image, (598, 98), (722, 222), (255, 255, 255), 2)  # Border
        cv2.rectangle(image, (600, 100), (720, 220), (200, 200, 200), -1)  # Card

    # Detect cards
    detected_cards = detector.detect_cards(image)

    # Print results
    print(f"Detected {len(detected_cards['hand_cards'])} hand cards")
    print(f"Detected {len(detected_cards['table_cards'])} table cards")

    # Print card details
    for i, card in enumerate(detected_cards['hand_cards']):
        print(f"Hand card {i + 1}: area={card['area']:.0f}, center={card['center']}")

    for i, card in enumerate(detected_cards['table_cards']):
        print(f"Table card {i + 1}: area={card['area']:.0f}, center={card['center']}")

    # Draw results
    result_image = detector.draw_detected_cards(image, detected_cards)

    # Display results (if running in an environment with display)
    try:
        plt.figure(figsize=(15, 10))

        # Show original image
        plt.subplot(2, 2, 1)
        plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        plt.title('Original Image')
        plt.axis('off')

        # Show preprocessed image
        plt.subplot(2, 2, 2)
        processed = detector.preprocess_image(image)
        plt.imshow(processed, cmap='gray')
        plt.title('Preprocessed (Edge Detection)')
        plt.axis('off')

        # Show detected cards
        plt.subplot(2, 2, 3)
        plt.imshow(cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB))
        plt.title('Detected Cards')
        plt.axis('off')

        # Show individual card regions
        plt.subplot(2, 2, 4)
        if detected_cards['hand_cards'] or detected_cards['table_cards']:
            # Extract first detected card as example
            all_cards = detected_cards['hand_cards'] + detected_cards['table_cards']
            if all_cards:
                sample_card = detector.extract_card_region(image, all_cards[0])
                plt.imshow(cv2.cvtColor(sample_card, cv2.COLOR_BGR2RGB))
                plt.title('Sample Extracted Card')
        plt.axis('off')

        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"Display not available: {e}")
        print("But detection completed successfully")

    return detected_cards, result_image


# Usage example:
if __name__ == "__main__":
    # Test with sample image
    detected_cards, result_image = test_card_detection("screenshots/img.png")

    # To use with your own image:
    # detected_cards, result_image = test_card_detection("path/to/your/poker_image.jpg")