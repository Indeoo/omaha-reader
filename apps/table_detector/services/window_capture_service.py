import os
from typing import List

from loguru import logger

from table_detector.domain.captured_window import CapturedWindow
from table_detector.utils.capture_utils import load_images_from_folder, get_poker_window_info, _capture_windows, \
    save_images_to_window_folders, capture_fullscreen
from table_detector.utils.windows_utils import write_windows_list


def capture_and_save_windows(timestamp_folder: str = None, save_windows=True, debug=False) -> List[CapturedWindow]:
    if debug:
        captured_images = load_images_from_folder(timestamp_folder)
        if captured_images:
            logger.info(f"✅ Loaded {len(captured_images)} images from debug folder")
        else:
            logger.error("❌ No images loaded from debug folder")
        return captured_images

    windows = get_poker_window_info("Pot Limit Omaha")
    if len(windows) > 0:
        logger.info(f"Found {len(windows)} poker windows with titles:")
        os.makedirs(timestamp_folder, exist_ok=True)
    else:
        return []

    captured_images = _capture_windows(windows=windows)

    if save_windows:
        full_screen = capture_fullscreen()

        full_screen_captured = CapturedWindow(
            image=full_screen,
            filename="full_screen.png",
            window_name='full_screen',
            description="Full screen"
        )
        captured_images.append(full_screen_captured)
        logger.info(f"Captured full screen")

        # Create window folder mapping - each window gets its own folder
        window_folder_mapping = {}
        for captured_image in captured_images:
            if captured_image.window_name != 'full_screen':
                # Create sanitized folder name
                safe_window_name = "".join(
                    [c if c.isalnum() or c in ('_', '-', ' ') else "_" for c in captured_image.window_name])
                safe_window_name = safe_window_name.strip().replace(' ', '_')
                window_folder = os.path.join(timestamp_folder, safe_window_name)
                window_folder_mapping[captured_image.window_name] = window_folder
            else:
                # Full screen goes to base folder
                window_folder_mapping[captured_image.window_name] = timestamp_folder

        # Save images to their respective window folders
        save_images_to_window_folders(captured_images, timestamp_folder, window_folder_mapping)

        # Write the window list to base folder
        write_windows_list(windows, timestamp_folder)

        # Remove full screen from the list before returning
        captured_images = [img for img in captured_images if img.window_name != 'full_screen']

    return captured_images


