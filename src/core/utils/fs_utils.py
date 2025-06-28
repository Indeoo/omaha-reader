import os
from datetime import datetime

DEBUG_FOLDER = "src/test/tables/test_move"


def create_timestamp_folder(DEBUG_MODE = False) -> str:
    """
    Create timestamp folder path for current session

    Returns:
        String path to timestamp folder
    """
    session_timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")

    if DEBUG_MODE:
        # Debug mode - use existing folder
        timestamp_folder = os.path.join(os.getcwd(),DEBUG_FOLDER)
    else:
        # Live mode - create new folder
        timestamp_folder = os.path.join(os.getcwd(), f"Dropbox/data_screenshots/{session_timestamp}")

    return timestamp_folder