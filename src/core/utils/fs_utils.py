import json
import os
from datetime import datetime

from loguru import logger

DEBUG_FOLDER = "src/test/tables/test_move"


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


# def write_dict(bids_data, timestamp_folder, window_name):
#     try:
#         # Create directory if it doesn't exist
#         os.makedirs(timestamp_folder, exist_ok=True)
#
#         # Create file path
#         file_path = os.path.join(timestamp_folder, f"result_{window_name}.txt")
#
#         # Check if we have data to write
#         if not bids_data:
#             logger.info("Warning: No bids data to write")
#             return
#
#         # Write as key-value pairs
#         with open(file_path, "w") as file:
#             for item, bid in bids_data.items():
#                 file.write(f"{item}: ${bid:.2f}\n")
#
#         logger.info(f"Bids written to: {file_path}")
#         logger.info(f"Successfully wrote {len(bids_data)} items")
#
#     except Exception as e:
#         logger.error(f"Error writing bids data: {e}")