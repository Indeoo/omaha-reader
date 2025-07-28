import numpy as np
from loguru import logger

from src.core.service.action_detection_service import detection_dict
from src.core.service.omaha_action_processor import group_moves_by_street


def get_street_actions(image: np.ndarray):
    detections = detection_dict(image)

    logger.info("Fixed")
    print(detections)

    return group_moves_by_street(detections)

