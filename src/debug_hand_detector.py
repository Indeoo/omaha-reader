import cv2
import numpy as np
from typing import Tuple, Dict
import os


class DebugHandDetector:
    def __init__(self):
        """
        Debug version to analyze why cards aren't being detected
        """
        self.hand_region_ratio = (0.42, 0.58, 0.53, 0.62)  # Middle area with cards

    def analyze_image(self, image_path: str):
        """
        Comprehensive analysis of the image to understand card detection issues
        """
        image = cv2.imread(image_path)
        if image is None:
            print(f"Could not load image: {image_path}")
            return None

        print(f"Image loaded: {image.shape}")

        # Step 1: Extract and analyze hand region
        hand_region, offset = self.extract_hand_region(image)
        print(f"Hand region extracted: {hand_region.shape}, offset: {offset}")

        # Step 2: Analyze colors in hand region
        self.analyze_colors(hand_region)

        # Step 3: Try different preprocessing methods
        preprocessed_results = self.test_preprocessing_methods(hand_region)

        # Step 4: Test contour detection with different parameters
        contour_results = self.test_contour_detection(hand_region, offset)

        # Step 5: Save debug images
        self.save_debug_images(image, hand_region, preprocessed_results, contour_results)

        return {
            'original': image,
            'hand_region': hand_region,
            'preprocessed': preprocessed_results,
            'contours': contour_results,
            'offset': offset
        }

    def extract_hand_region(self, image: np.ndarray) -> Tuple[np.ndarray, Tuple[int, int]]:
        """Extract hand region and show boundaries"""
        height, width = image.shape[:2]

        x1 = int(width * self.hand_region_ratio[0])  # 25%
        x2 = int(width * self.hand_region_ratio[1])  # 75%
        y1 = int(height * self.hand_region_ratio[2])  # 65%
        y2 = int(height * self.hand_region_ratio[3])  # 95%

        print(f"Hand region boundaries: x1={x1}, x2={x2}, y1={y1}, y2={y2}")
        print(f"Region size: {x2 - x1} x {y2 - y1}")

        hand_region = image[y1:y2, x1:x2]
        offset = (x1, y1)

        return hand_region, offset

    def analyze_colors(self, hand_region: np.ndarray):
        """Analyze color distribution in hand region"""
        if hand_region.size == 0:
            print("Hand region is empty!")
            return

        # Convert to different color spaces
        hsv = cv2.cvtColor(hand_region, cv2.COLOR_BGR2HSV)

        # Get color statistics
        bgr_mean = np.mean(hand_region, axis=(0, 1))
        hsv_mean = np.mean(hsv, axis=(0, 1))

        print(f"BGR mean colors: B={bgr_mean[0]:.1f}, G={bgr_mean[1]:.1f}, R={bgr_mean[2]:.1f}")
        print(f"HSV mean colors: H={hsv_mean[0]:.1f}, S={hsv_mean[1]:.1f}, V={hsv_mean[2]:.1f}")

        # Analyze blue pixels with different thresholds
        blue_ranges = [
            ([80, 40, 40], [140, 255, 255]),  # Very broad
            ([90, 60, 60], [130, 255, 255]),  # Medium
            ([100, 80, 80], [120, 255, 255]),  # Narrow
            ([105, 100, 100], [125, 255, 255])  # Very narrow
        ]

        for i, (lower, upper) in enumerate(blue_ranges):
            mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
            blue_pixels = cv2.countNonZero(mask)
            total_pixels = hand_region.shape[0] * hand_region.shape[1]
            percentage = (blue_pixels / total_pixels) * 100
            print(f"Blue range {i + 1}: {blue_pixels}/{total_pixels} pixels ({percentage:.2f}%)")

    def test_preprocessing_methods(self, hand_region: np.ndarray) -> Dict:
        """Test different preprocessing approaches"""
        if hand_region.size == 0:
            return {}

        results = {}

        # Method 1: HSV Blue detection
        hsv = cv2.cvtColor(hand_region, cv2.COLOR_BGR2HSV)
        lower_blue = np.array([80, 40, 40])
        upper_blue = np.array([140, 255, 255])
        blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
        results['blue_mask'] = blue_mask

        # Method 2: Edge detection
        gray = cv2.cvtColor(hand_region, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 30, 100)
        results['edges'] = edges

        # Method 3: Combined
        combined = cv2.bitwise_or(blue_mask, edges)
        results['combined'] = combined

        # Method 4: Threshold on grayscale
        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        results['threshold'] = thresh

        # Method 5: Adaptive threshold
        adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                         cv2.THRESH_BINARY, 11, 2)
        results['adaptive'] = adaptive

        # Print statistics for each method
        for name, result in results.items():
            white_pixels = cv2.countNonZero(result)
            total = result.shape[0] * result.shape[1]
            print(f"{name}: {white_pixels}/{total} white pixels ({white_pixels / total * 100:.1f}%)")

        return results

    def test_contour_detection(self, hand_region: np.ndarray, offset: Tuple[int, int]) -> Dict:
        """Test contour detection with different methods"""
        if hand_region.size == 0:
            return {}

        results = {}

        # Test on different preprocessed images
        hsv = cv2.cvtColor(hand_region, cv2.COLOR_BGR2HSV)
        blue_mask = cv2.inRange(hsv, np.array([80, 40, 40]), np.array([140, 255, 255]))

        gray = cv2.cvtColor(hand_region, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 30, 100)

        test_images = {
            'blue_mask': blue_mask,
            'edges': edges,
            'combined': cv2.bitwise_or(blue_mask, edges)
        }

        for name, test_img in test_images.items():
            # Find contours
            contours, _ = cv2.findContours(test_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            print(f"\n{name}: Found {len(contours)} contours")

            # Analyze each contour
            valid_contours = []
            for i, contour in enumerate(contours):
                area = cv2.contourArea(contour)
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h > 0 else 0

                print(f"  Contour {i}: area={area:.0f}, size={w}x{h}, ratio={aspect_ratio:.2f}")

                # Very loose criteria for debugging
                if area > 500 and w > 15 and h > 20:
                    valid_contours.append({
                        'contour': contour,
                        'area': area,
                        'bounding_rect': (x + offset[0], y + offset[1], w, h),
                        'aspect_ratio': aspect_ratio
                    })

            results[name] = {
                'total_contours': len(contours),
                'valid_contours': valid_contours,
                'processed_image': test_img
            }

            print(f"  Valid contours: {len(valid_contours)}")

        return results

    def save_debug_images(self, original: np.ndarray, hand_region: np.ndarray,
                          preprocessed: Dict, contours: Dict):
        """Save debug images to understand what's happening"""
        debug_dir = "debug_images"
        os.makedirs(debug_dir, exist_ok=True)

        # Save original with hand region marked
        debug_original = original.copy()
        height, width = original.shape[:2]
        x1 = int(width * self.hand_region_ratio[0])
        x2 = int(width * self.hand_region_ratio[1])
        y1 = int(height * self.hand_region_ratio[2])
        y2 = int(height * self.hand_region_ratio[3])

        cv2.rectangle(debug_original, (x1, y1), (x2, y2), (0, 255, 255), 3)
        cv2.putText(debug_original, "Hand Region", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        cv2.imwrite(f"{debug_dir}/01_original_with_region.png", debug_original)

        # Save hand region
        cv2.imwrite(f"{debug_dir}/02_hand_region.png", hand_region)

        # Save preprocessed images
        for i, (name, img) in enumerate(preprocessed.items()):
            cv2.imwrite(f"{debug_dir}/03_{i}_{name}.png", img)

        # Save contour results
        for name, result in contours.items():
            if 'processed_image' in result:
                # Draw contours on the processed image
                contour_img = cv2.cvtColor(result['processed_image'], cv2.COLOR_GRAY2BGR)

                for j, contour_info in enumerate(result['valid_contours']):
                    contour = contour_info['contour']
                    x, y, w, h = contour_info['bounding_rect']

                    # Adjust coordinates back to hand region
                    x_local = x - int(original.shape[1] * self.hand_region_ratio[0])
                    y_local = y - int(original.shape[0] * self.hand_region_ratio[2])

                    cv2.drawContours(contour_img, [contour], -1, (0, 255, 0), 2)
                    cv2.rectangle(contour_img, (x_local, y_local),
                                  (x_local + w, y_local + h), (255, 0, 0), 1)
                    cv2.putText(contour_img, f"{j}", (x_local, y_local - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

                cv2.imwrite(f"{debug_dir}/04_contours_{name}.png", contour_img)

        print(f"\nDebug images saved to {debug_dir}/ directory")

    def suggest_parameters(self, analysis_results: Dict):
        """Suggest parameter adjustments based on analysis"""
        print("\n" + "=" * 50)
        print("PARAMETER SUGGESTIONS:")
        print("=" * 50)

        if not analysis_results:
            print("No analysis results available")
            return

        contours = analysis_results.get('contours', {})

        # Find the method with most valid contours
        best_method = None
        max_contours = 0

        for name, result in contours.items():
            if len(result['valid_contours']) > max_contours:
                max_contours = len(result['valid_contours'])
                best_method = name

        print(f"Best detection method: {best_method} with {max_contours} valid contours")

        if best_method and max_contours > 0:
            valid_contours = contours[best_method]['valid_contours']

            # Analyze areas
            areas = [c['area'] for c in valid_contours]
            aspect_ratios = [c['aspect_ratio'] for c in valid_contours]

            print(f"Area range found: {min(areas):.0f} - {max(areas):.0f}")
            print(f"Aspect ratio range: {min(aspect_ratios):.2f} - {max(aspect_ratios):.2f}")

            # Suggest new parameters
            area_min = int(min(areas) * 0.8)
            area_max = int(max(areas) * 1.2)
            ratio_min = max(0.4, min(aspect_ratios) * 0.9)
            ratio_max = min(2.0, max(aspect_ratios) * 1.1)

            print(f"\nSuggested parameters:")
            print(f"  card_area_range = ({area_min}, {area_max})")
            print(f"  aspect_ratio_range = ({ratio_min:.2f}, {ratio_max:.2f})")

            if best_method == 'blue_mask':
                print(f"  Use blue color detection")
            elif best_method == 'edges':
                print(f"  Use edge detection")
            else:
                print(f"  Use combined approach")
        else:
            print("No valid contours found. Suggestions:")
            print("1. Check if the hand region is correctly positioned")
            print("2. Try different color ranges")
            print("3. Adjust preprocessing parameters")
            print("4. Check if cards are visible in the screenshot")


def debug_hand_detection(image_path: str):
    """
    Debug the hand card detection process
    """
    detector = DebugHandDetector()

    print("Starting debug analysis...")
    print("=" * 50)

    results = detector.analyze_image(image_path)

    if results:
        detector.suggest_parameters(results)
        print(f"\nCheck the debug_images/ folder for visual analysis")

    return results