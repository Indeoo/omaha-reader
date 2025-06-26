import cv2
import numpy as np
from typing import List, Tuple, Dict
from concurrent.futures import ThreadPoolExecutor


def find_template_matches_parallel(
        image: np.ndarray,
        templates: Dict[str, np.ndarray],
        search_region: Tuple[float, float, float, float] = None,
        scale_factors: List[float] = None,
        match_threshold: float = 0.955,
        min_card_size: int = 20,
        max_workers: int = 4
) -> List[Dict]:
    """
    Find matches for all templates in the image using parallel execution

    Args:
        image: Input image
        templates: Dictionary of template_name -> template_image
        search_region: (left, top, right, bottom) as ratios of image size
        scale_factors: List of scale factors to try
        match_threshold: Minimum match score to consider
        min_card_size: Minimum card size in pixels
        max_workers: Maximum number of parallel workers

    Returns:
        List of detection dictionaries
    """
    if scale_factors is None:
        scale_factors = [1.0]

    all_detections = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all template matching tasks in parallel
        futures = []
        for template_name, template in templates.items():
            future = executor.submit(
                find_single_template_matches,
                image, template, template_name,
                search_region, scale_factors, match_threshold, min_card_size
            )
            futures.append(future)

        # Collect results
        for future in futures:
            detections = future.result()
            all_detections.extend(detections)

    return all_detections


def find_single_template_matches(
        image: np.ndarray,
        template: np.ndarray,
        template_name: str,
        search_region: Tuple[float, float, float, float] = None,
        scale_factors: List[float] = None,
        match_threshold: float = 0.955,
        min_card_size: int = 20
) -> List[Dict]:
    """
    Find all matches of a single template in the image at multiple scales

    Args:
        image: Input image
        template: Template image
        template_name: Name of the template
        search_region: (left, top, right, bottom) as ratios of image size
        scale_factors: List of scale factors to try
        match_threshold: Minimum match score to consider
        min_card_size: Minimum card size in pixels

    Returns:
        List of detection dictionaries
    """
    if scale_factors is None:
        scale_factors = [1.0]

    try:
        detections = []
        search_image, offset = extract_search_region(image, search_region)
        template_h, template_w = template.shape[:2]

        for scale in scale_factors:
            scale_detections = match_template_at_scale(
                search_image, template, template_name, scale,
                template_w, template_h, offset, match_threshold, min_card_size
            )
            detections.extend(scale_detections)

    except Exception as e:
        print(f"{e} template name: {template_name}")
        raise e

    return detections


def match_template_at_scale(
        search_image: np.ndarray,
        template: np.ndarray,
        template_name: str,
        scale: float,
        template_w: int,
        template_h: int,
        offset: Tuple[int, int],
        match_threshold: float = 0.955,
        min_card_size: int = 20
) -> List[Dict]:
    """
    Perform template matching at a specific scale

    Args:
        search_image: Image region to search in
        template: Template image
        template_name: Name of the template
        scale: Scale factor
        template_w: Template width
        template_h: Template height
        offset: (x, y) offset of search region
        match_threshold: Minimum match score to consider
        min_card_size: Minimum card size in pixels

    Returns:
        List of detection dictionaries
    """
    scaled_w = int(template_w * scale)
    scaled_h = int(template_h * scale)

    # Skip if template becomes too small or too large
    if (scaled_w < min_card_size or scaled_h < min_card_size or
            scaled_w > search_image.shape[1] or scaled_h > search_image.shape[0]):
        return []

    # Resize template
    scaled_template = cv2.resize(template, (scaled_w, scaled_h))

    # Perform template matching
    result = cv2.matchTemplate(search_image, scaled_template, cv2.TM_CCORR_NORMED)

    # Find all locations where match is above threshold
    locations = np.where(result >= match_threshold)
    detections = []

    for y, x in zip(*locations):
        match_score = result[y, x]
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


def extract_search_region(
        image: np.ndarray,
        search_region: Tuple[float, float, float, float] = None
) -> Tuple[np.ndarray, Tuple[int, int]]:
    """
    Extract the search region from the image

    Args:
        image: Input image
        search_region: (left, top, right, bottom) as ratios of image size

    Returns:
        Tuple of (extracted region, (x_offset, y_offset))
    """
    if search_region is None:
        return image, (0, 0)

    height, width = image.shape[:2]
    x1 = int(width * search_region[0])
    y1 = int(height * search_region[1])
    x2 = int(width * search_region[2])
    y2 = int(height * search_region[3])

    region = image[y1:y2, x1:x2]
    return region, (x1, y1)


def filter_overlapping_detections(
        detections: List[Dict],
        overlap_threshold: float = 0.3
) -> List[Dict]:
    """
    Remove overlapping detections, keeping the ones with highest match scores

    Args:
        detections: List of detection dictionaries
        overlap_threshold: Maximum allowed overlap ratio

    Returns:
        Filtered list of detections
    """
    if not detections:
        return []

    # Sort by match score (highest first)
    detections.sort(key=lambda x: x['match_score'], reverse=True)
    filtered = []

    for detection in detections:
        if not overlaps_with_existing(detection, filtered, overlap_threshold):
            filtered.append(detection)

    return filtered


def overlaps_with_existing(
        detection: Dict,
        accepted_detections: List[Dict],
        overlap_threshold: float = 0.3
) -> bool:
    """
    Check if detection overlaps significantly with any already accepted detection

    Args:
        detection: Detection to check
        accepted_detections: List of already accepted detections
        overlap_threshold: Maximum allowed overlap ratio

    Returns:
        True if overlaps, False otherwise
    """
    for accepted in accepted_detections:
        overlap = calculate_overlap_ratio(
            detection['bounding_rect'],
            accepted['bounding_rect']
        )
        if overlap > overlap_threshold:
            return True
    return False


def calculate_overlap_ratio(
        rect1: Tuple[int, int, int, int],
        rect2: Tuple[int, int, int, int]
) -> float:
    """
    Calculate the overlap ratio between two rectangles

    Args:
        rect1: (x, y, width, height)
        rect2: (x, y, width, height)

    Returns:
        Overlap ratio (intersection over union)
    """
    x1, y1, w1, h1 = rect1
    x2, y2, w2, h2 = rect2

    # Calculate intersection
    x_overlap = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
    y_overlap = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))

    if x_overlap == 0 or y_overlap == 0:
        return 0.0

    intersection_area = x_overlap * y_overlap
    area1 = w1 * h1
    area2 = w2 * h2
    union_area = area1 + area2 - intersection_area

    return intersection_area / union_area if union_area > 0 else 0.0


def sort_detections_by_position(
        detections: List[Dict],
        sort_by: str = 'x'
) -> List[Dict]:
    """
    Sort detections by position

    Args:
        detections: List of detection dictionaries
        sort_by: 'x' for left to right, 'y' for top to bottom

    Returns:
        Sorted list of detections
    """
    if sort_by == 'x':
        return sorted(detections, key=lambda d: d['center'][0])
    elif sort_by == 'y':
        return sorted(detections, key=lambda d: d['center'][1])
    else:
        raise ValueError(f"Invalid sort_by value: {sort_by}")