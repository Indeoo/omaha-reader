import os
import cv2
import numpy as np
from typing import List, Tuple, Dict

from src.utils.template_loader import load_templates


class PokerHandDetector:
    def __init__(self, templates_dir: str = "resources/templates/hand_cards/"):
        """
        Template-first detector that scans the entire image directly with templates
        No preprocessing, no assumptions about colors or regions

        Args:
            templates_dir: Directory containing hand card templates
        """
        self.search_region = (0.0, 0.5, 1.0, 1.0)  # Middle area with cards

        self.templates_dir = templates_dir
        self.templates = load_templates(self.templates_dir)

        # Template matching parameters
        self.match_threshold = 0.6
        self.scale_factors = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5]

    def detect_hand_cards(self, image: np.ndarray) -> List[Dict]:
        """
        Detect hand cards by directly scanning the entire image with each template
        No preprocessing - templates and image used as-is
        """
        if not self.templates:
            print("No templates loaded!")
            return []

        all_detections = []

        # For each template, scan the entire image
        for template_name, template in self.templates.items():
            detections = self.find_template_matches(image, template, template_name)
            all_detections.extend(detections)

        # Remove overlapping detections (keep best matches)
        filtered_detections = self.remove_overlapping_detections(all_detections)

        # Sort by x-coordinate (left to right)
        filtered_detections.sort(key=lambda x: x['center'][0])

        return filtered_detections

    def extract_search_region(self, image: np.ndarray) -> Tuple[np.ndarray, Tuple[int, int]]:
        """Extract the search region from the image"""
        if self.search_region is None:
            return image, (0, 0)

        height, width = image.shape[:2]
        x1 = int(width * self.search_region[0])
        y1 = int(height * self.search_region[1])
        x2 = int(width * self.search_region[2])
        y2 = int(height * self.search_region[3])

        region = image[y1:y2, x1:x2]
        return region, (x1, y1)

    def find_template_matches(self, image: np.ndarray, template: np.ndarray, template_name: str) -> List[Dict]:
        """
        Find all matches of a single template in the image at multiple scales
        """
        detections = []

        search_image, offset = self.extract_search_region(image)

        # Get template dimensions
        template_h, template_w = template.shape[:2]

        # Try multiple scales
        for scale in self.scale_factors:
            # Resize template
            scaled_w = int(template_w * scale)
            scaled_h = int(template_h * scale)

            # Skip if template becomes too small or too large (check against search_image, not full image)
            if scaled_w < 20 or scaled_h < 20 or scaled_w > search_image.shape[1] or scaled_h > search_image.shape[0]:
                continue

            scaled_template = cv2.resize(template, (scaled_w, scaled_h))

            # Perform template matching on SEARCH_IMAGE, not full image
            result = cv2.matchTemplate(search_image, scaled_template, cv2.TM_CCOEFF_NORMED)

            # Find all locations where match is above threshold
            locations = np.where(result >= self.match_threshold)

            for y, x in zip(*locations):
                match_score = result[y, x]

                # Calculate center and bounding box (add offset to map back to full image coordinates)
                center_x = x + scaled_w // 2
                center_y = y + scaled_h // 2

                detection = {
                    'template_name': template_name,
                    'match_score': float(match_score),
                    'bounding_rect': (x + offset[0], y + offset[1], scaled_w, scaled_h),
                    'center': (center_x + offset[0], center_y + offset[1]),
                    'scale': scale,
                    'template_size': (template_w, template_h),
                    'scaled_size': (scaled_w, scaled_h)
                }

                detections.append(detection)

        return detections

    def remove_overlapping_detections(self, detections: List[Dict], overlap_threshold: float = 0.3) -> List[Dict]:
        """
        Remove overlapping detections, keeping the ones with highest match scores
        """
        if not detections:
            return []

        # Sort by match score (highest first)
        detections.sort(key=lambda x: x['match_score'], reverse=True)

        filtered = []

        for detection in detections:
            # Check if this detection overlaps significantly with any already accepted detection
            is_overlapping = False

            for accepted in filtered:
                overlap = self.calculate_overlap(detection['bounding_rect'], accepted['bounding_rect'])
                if overlap > overlap_threshold:
                    is_overlapping = True
                    break

            if not is_overlapping:
                filtered.append(detection)

        return filtered

    def calculate_overlap(self, rect1: Tuple[int, int, int, int], rect2: Tuple[int, int, int, int]) -> float:
        """
        Calculate the overlap ratio between two rectangles
        """
        x1, y1, w1, h1 = rect1
        x2, y2, w2, h2 = rect2

        # Calculate intersection
        x_overlap = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
        y_overlap = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))

        if x_overlap == 0 or y_overlap == 0:
            return 0.0

        intersection_area = x_overlap * y_overlap

        # Calculate union
        area1 = w1 * h1
        area2 = w2 * h2
        union_area = area1 + area2 - intersection_area

        if union_area == 0:
            return 0.0

        return intersection_area / union_area

    def extract_detected_regions(self, image: np.ndarray, detections: List[Dict]) -> List[Dict]:
        """
        Extract the actual image regions for each detection
        """
        results = []

        for detection in detections:
            x, y, w, h = detection['bounding_rect']

            # Extract the region from original image
            card_region = image[y:y + h, x:x + w].copy()

            # Create enhanced detection info
            enhanced_detection = detection.copy()
            enhanced_detection['card_region'] = card_region
            enhanced_detection['area'] = w * h
            enhanced_detection['aspect_ratio'] = w / h if h > 0 else 0

            results.append(enhanced_detection)

        return results

    def draw_detected_cards(self, image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """
        Draw detected cards on the image
        """
        result = image.copy()

        for i, detection in enumerate(detections):
            x, y, w, h = detection['bounding_rect']

            # Draw bounding rectangle
            cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Draw center point
            center = detection['center']
            cv2.circle(result, center, 5, (255, 0, 0), -1)

            # Add label with template name and confidence
            label = f"{detection['template_name']} ({detection['match_score']:.2f})"
            cv2.putText(result, label, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Add scale info
            scale_info = f"Scale: {detection['scale']:.1f}"
            cv2.putText(result, scale_info, (x, y + h + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)

        return result

    def get_detection_summary(self, detections: List[Dict]) -> Dict:
        """
        Get summary information about detections
        """
        if not detections:
            return {
                "total": 0,
                "cards": {},
                "average_confidence": 0.0,  # Add this line
                "scales_used": []  # Add this line
            }

        summary = {
            "total": len(detections),
            "cards": {},
            "average_confidence": sum(d['match_score'] for d in detections) / len(detections),
            "scales_used": sorted(list(set(d['scale'] for d in detections)))
        }

        # Count each card type
        for detection in detections:
            card_name = detection['template_name']
            if card_name not in summary["cards"]:
                summary["cards"][card_name] = 0
            summary["cards"][card_name] += 1

        return summary

def test_template_first_detection(image_path: str, templates_dir: str = "resources/templates/hand_cards/"):
    """
    Test the template-first detection approach
    """
    detector = PokerHandDetector(templates_dir=templates_dir)

    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Could not load image: {image_path}")
        return None

    print(f"Loaded image: {image.shape}")
    print(f"Loaded {len(detector.templates)} templates")

    # Detect cards using template-first approach
    detections = detector.detect_hand_cards(image)

    # Extract regions for each detection
    detections_with_regions = detector.extract_detected_regions(image, detections)

    # Get summary
    summary = detector.get_detection_summary(detections)

    print(f"\nDetection Summary:")
    print(f"Total detections: {summary['total']}")
    print(f"Average confidence: {summary['average_confidence']:.3f}")
    print(f"Scales used: {summary['scales_used']}")
    print(f"Cards found: {summary['cards']}")

    # Print detailed results
    print(f"\nDetailed Results:")
    for i, detection in enumerate(detections_with_regions):
        print(f"  Detection {i + 1}:")
        print(f"    Template: {detection['template_name']}")
        print(f"    Confidence: {detection['match_score']:.3f}")
        print(f"    Position: {detection['center']}")
        print(f"    Size: {detection['scaled_size']}")
        print(f"    Scale: {detection['scale']:.1f}")
        print()

    # Create visualization
    result_image = detector.draw_detected_cards(image, detections)

    return {
        'original': image,
        'result_image': result_image,
        'detections': detections_with_regions,
        'summary': summary
    }


def save_detected_cards_template_first(results, output_dir="detected_cards_template_first"):
    """
    Save each detected card region
    """
    os.makedirs(output_dir, exist_ok=True)

    detections = results['detections']

    for i, detection in enumerate(detections):
        card_region = detection['card_region']
        template_name = detection['template_name']
        confidence = detection['match_score']
        scale = detection['scale']

        filename = f"{output_dir}/{template_name}_conf{confidence:.2f}_scale{scale:.1f}_{i}.png"
        cv2.imwrite(filename, card_region)
        print(f"Saved: {filename}")

    return len(detections)
