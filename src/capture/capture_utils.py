import os
from datetime import datetime
from typing import List, Dict, Any, Tuple

from PIL import ImageGrab

from src.capture.windows_utils import get_window_info, careful_capture_window, capture_screen_region, write_windows_list


def _capture_windows(log_mode: str = "none", log_file_path: str = None, timestamp_folder: str = None) -> Tuple[
    List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Capture windows with configurable logging

    Args:
        log_mode: Logging mode - "none", "console", or "file"
        log_file_path: Custom path for log file. If None, uses timestamp-based name

    Returns:
        Tuple of (captured_images, windows, timestamp_used)
    """

    def log_message(message: str):
        """Helper function to log messages based on the mode"""
        if log_mode == "none":
            return
        elif log_mode == "file" and log_file:
            log_file.write(message + '\n')
            log_file.flush()  # Ensure immediate write
        elif log_mode == "console":
            print(message)

    # Setup logging file if needed
    log_file = None
    if log_mode == "file":
        if log_file_path is None:
            log_file_path = f"capture_log_{timestamp_folder}.txt"

        try:
            log_file = open(log_file_path, 'w', encoding='utf-8')
            log_file.write(f"Window Capture Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            log_file.write("=" * 60 + "\n\n")
        except Exception as e:
            print(f"Error opening log file {log_file_path}: {e}")
            print("Falling back to console logging")
            log_mode = "console"

    try:
        # Get all window info
        windows = get_window_info()
        log_message(f"Found {len(windows)} windows to capture")

        # List to store all captured images with their metadata
        captured_images = []

        # First, capture the full screen
        try:
            full_screen = ImageGrab.grab()
            captured_images.append({
                'image': full_screen,
                'filename': "full_screen.png",
                'description': "Full screen",
                'window_name': 'full_screen'
            })
            log_message(f"Captured full screen")
        except Exception as e:
            log_message(f"Error capturing full screen: {e}")
            full_screen = None

        # Capture each window and store in memory
        for i, window in enumerate(windows, 1):
            hwnd = window['hwnd']
            title = window['title']
            process = window['process']
            rect = window['rect']
            width = window['width']
            height = window['height']

            log_message(f"Capturing window {i}/{len(windows)}: {title} ({process})")

            # if "Lobby" not in title and "TableCover" not in title and "Pot Limit Omaha" not in title:
            #     continue

            if "Lobby" not in title and "Pot Limit Omaha" not in title:
                continue

            # Create filename
            safe_title = "".join([c if c.isalnum() else "_" for c in title])[:50]
            safe_process = "".join([c if c.isalnum() else "_" for c in process])[:20]
            filename = f"{i:02d}_{safe_process}_{safe_title}.png"

            # First try using PrintWindow method (ignores overlapping)
            img = careful_capture_window(hwnd, width, height)
            capture_method = "PrintWindow (no overlap)"

            # If that fails, fall back to screen region capture
            if img is None and full_screen is not None:
                log_message("  Using fallback method: screen region capture")
                img = capture_screen_region(rect)
                capture_method = "Screen region (with overlap)"

            if img:
                captured_images.append({
                    'image': img,
                    'filename': filename,
                    'description': f"{title} ({process}) - {capture_method}",
                    'window_name': title
                })
                log_message(f"  ✓ Captured using {capture_method}")
            else:
                log_message(f"  ✗ Failed to capture")

        return captured_images, windows

    finally:
        # Close log file if it was opened
        if log_file:
            log_file.close()


def _save_windows(
        captured_images: List[Dict[str, Any]],
        windows: List[Dict[str, Any]],
        timestamp_folder: str = None,
        log_mode: str = "none", log_file_path: str = None
):
    """
    Save captured windows with configurable logging

    Args:
        captured_images: List of captured image dictionaries
        windows: List of window information dictionaries
        log_mode: Logging mode - "none", "console", or "file"
        log_file_path: Custom path for log file. If None, uses timestamp-based name

    Returns:
        str: Path to the output folder where images were saved
    """

    def log_message(message: str):
        """Helper function to log messages based on the mode"""
        if log_mode == "none":
            return
        elif log_mode == "file" and log_file:
            log_file.write(message + '\n')
            log_file.flush()  # Ensure immediate write
        elif log_mode == "console":
            print(message)

    # Setup logging file if needed
    log_file = None
    if log_mode == "file":
        if log_file_path is None:
            log_file_path = f"save_log_{timestamp_folder}.txt"

        try:
            log_file = open(log_file_path, 'w', encoding='utf-8')
            log_file.write(f"Window Save Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            log_file.write("=" * 60 + "\n\n")
        except Exception as e:
            print(f"Error opening log file {log_file_path}: {e}")
            print("Falling back to console logging")
            log_mode = "console"

    try:
        # Now save all captured images in a separate loop
        log_message(f"\nSaving {len(captured_images)} captured images...")
        successes = 0

        log_message(f"Screenshots will be saved to: {timestamp_folder}")

        # Write the window list to windows.txt
        write_windows_list(windows, timestamp_folder)

        for i, captured_item in enumerate(captured_images, 1):
            try:
                filepath = os.path.join(timestamp_folder, captured_item['filename'])
                captured_item['image'].save(filepath)
                log_message(f"  ✓ Saved {i}/{len(captured_images)}: {captured_item['filename']}")
                successes += 1
            except Exception as e:
                log_message(f"  ✗ Failed to save {captured_item['filename']}: {e}")

        # Print summary
        log_message("\n---- Capture Summary ----")
        log_message(f"Total windows found: {len(windows)}")
        log_message(f"Images captured in memory: {len(captured_images)}")
        log_message(f"Successfully saved to disk: {successes}")
        log_message(f"Screenshots saved to: {timestamp_folder}")
        log_message("Screenshot process completed.")

    finally:
        # Close log file if it was opened
        if log_file:
            log_file.close()


def capture_and_save_windows(log_mode: str = "none", log_file_path: str = None, timestamp_folder: str = None,
                             save_windows=True) -> Tuple[
    List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Convenience function that captures and saves windows in one call with consistent timestamp

    Args:
        log_mode: Logging mode - "none", "console", or "file"
        log_file_path: Custom path for log file. If None, uses timestamp-based name

    Returns:
        Tuple of (output_folder_path, captured_images, windows)
    """

    # Capture windows with the timestamp
    captured_images, windows = _capture_windows(log_mode=log_mode, log_file_path=log_file_path,
                                                timestamp_folder=timestamp_folder)

    # Save windows with the same timestamp
    if save_windows:
        _save_windows(
            captured_images, windows,
            timestamp_folder=timestamp_folder,
            log_mode=log_mode,
            log_file_path=log_file_path
        )

    return captured_images, windows
