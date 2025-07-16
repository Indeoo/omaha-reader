import json
import os
from datetime import datetime

from loguru import logger

DEBUG_FOLDER = "src/test/resources/tables/test_move"


def create_timestamp_folder(DEBUG_MODE=False) -> str:
    """
    Create timestamp folder path for current session

    Returns:
        String path to timestamp folder
    """
    now = datetime.now()
    date_folder = now.strftime("%Y_%m_%d")
    time_folder = now.strftime("%H%M%S")

    if DEBUG_MODE:
        # Debug mode - use existing folder
        timestamp_folder = os.path.join(os.getcwd(), DEBUG_FOLDER)
    else:
        # Live mode - create new folder 
        timestamp_folder = os.path.join(os.getcwd(), "resources/results", date_folder, time_folder)

    return timestamp_folder


def get_image_names(timestamp_folder):
    # Get all image files in the folder
    image_extensions = ('.png')
    image_files = [f for f in os.listdir(timestamp_folder)
                   if f.lower().endswith(image_extensions) and not f.lower().endswith('_result.png')
                   and not f.lower() == 'full_screen.png']
    return image_files


def create_window_folder(base_timestamp_folder: str, window_name: str) -> str:
    # Sanitize window name for folder creation
    safe_window_name = "".join([c if c.isalnum() or c in ('_', '-', ' ') else "_" for c in window_name])
    safe_window_name = safe_window_name.strip().replace(' ', '_')

    window_folder = os.path.join(base_timestamp_folder, safe_window_name)

    try:
        os.makedirs(window_folder, exist_ok=True)
        logger.info(f"📁 Created window folder: {window_folder}")
    except Exception as e:
        logger.error(f"❌ Error creating window folder {window_folder}: {str(e)}")
        # Fallback to base folder if window folder creation fails
        return base_timestamp_folder

    return window_folder
