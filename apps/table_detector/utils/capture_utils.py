import os
from typing import List, Dict

from PIL import ImageGrab, Image
from loguru import logger

from shared.domain.domain.captured_window import CapturedWindow
from table_detector.utils.fs_utils import get_image_names
from table_detector.utils.windows_utils import get_window_info, careful_capture_window, capture_screen_region, \
    write_windows_list


def _capture_windows(windows) -> List[CapturedWindow]:
    windows.sort(key=lambda w: w['hwnd'])

    logger.info(f"Found {len(windows)} windows to capture")

    captured_images = []

    for i, window in enumerate(windows, 1):
        hwnd = window['hwnd']
        title = window['title']
        process = window['process']
        rect = window['rect']
        width = window['width']
        height = window['height']

        logger.info(f"Capturing window {i}/{len(windows)}: {title} ({process})")

        safe_title = "".join([c if c.isalnum() else "_" for c in title])[:50]
        safe_title = f"{i:02d}_{safe_title}"
        filename = f"{safe_title}.png"

        img = careful_capture_window(hwnd, width, height)

        if img is None:
            logger.info("  Using fallback method: screen region capture")
            img = capture_screen_region(rect)

        if img:
            captured_image = CapturedWindow(
                image=img,
                filename=filename,
                window_name=safe_title,
                description=f"{safe_title}"
            )
            captured_images.append(captured_image)
            logger.info(f"  ✓ Captured images")
        else:
            logger.error(f"  ✗ Failed to capture")

    return captured_images


def get_poker_window_info(poker_window_name):
    original_windows_info = get_window_info()
    windows = [w for w in original_windows_info if poker_window_name in w['title']]
    return windows


def save_images_to_window_folders(
        captured_images: List[CapturedWindow],
        base_folder: str,
        window_folder_mapping: Dict[str, str]
):
    logger.info(f"\nSaving {len(captured_images)} captured images to window-specific folders...")
    successes = 0

    for i, captured_image in enumerate(captured_images, 1):
        try:
            window_name = captured_image.window_name
            window_folder = window_folder_mapping.get(window_name, base_folder)

            # Ensure the window folder exists
            os.makedirs(window_folder, exist_ok=True)

            filepath = os.path.join(window_folder, captured_image.filename)
            if captured_image.save(filepath):
                logger.info(f"  ✓ Saved {i}/{len(captured_images)}: {captured_image.filename} → {window_folder}")
                successes += 1
            else:
                logger.info(f"  ✗ Failed to save {captured_image.filename}")
        except Exception as e:
            logger.info(f"  ✗ Failed to save {captured_image.filename}: {e}")

    logger.info(f"\n---- Capture Summary ----")
    logger.info(f"Images captured in memory: {len(captured_images)}")
    logger.info(f"Successfully saved to disk: {successes}")
    logger.info("Screenshot process completed.")


def _load_images_from_folder(timestamp_folder: str) -> List[CapturedWindow]:
    captured_images = []

    if not os.path.exists(timestamp_folder):
        logger.error(f"❌ Debug folder not found: {timestamp_folder}")
        return captured_images

    image_files = get_image_names(timestamp_folder)

    logger.info(f"🔍 Loading {len(image_files)} images from debug folder: {timestamp_folder}")

    for filename in sorted(image_files):
        try:
            filepath = os.path.join(timestamp_folder, filename)
            # Load image and create a copy to avoid file handle leaks
            with Image.open(filepath) as source_image:
                # Create a copy so we can close the original file handle
                image = source_image.copy()

            window_name = filename.replace('.png', '')

            captured_image = CapturedWindow(
                image=image,
                filename=filename,
                window_name=window_name,
                description="Loaded from debug folder"
            )
            captured_images.append(captured_image)
            logger.info(f"  ✓ Loaded: {filename} → window: {window_name}")

        except Exception as e:
            logger.error(f"  ❌ Failed to load {filename}: {str(e)}")

    return captured_images


def capture_and_save_windows(timestamp_folder: str = None, save_windows=True, debug=False) -> List[CapturedWindow]:
    if debug:
        captured_images = _load_images_from_folder(timestamp_folder)
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
        try:
            with ImageGrab.grab() as full_screen_source:
                # Create a copy to avoid keeping the original reference
                full_screen = full_screen_source.copy()
            
            full_screen_captured = CapturedWindow(
                image=full_screen,
                filename="full_screen.png",
                window_name='full_screen',
                description="Full screen"
            )
            captured_images.append(full_screen_captured)
            logger.info(f"Captured full screen")
        except Exception as e:
            logger.error(f"Error capturing full screen: {e}")

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