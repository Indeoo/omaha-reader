import os
from typing import List
import ctypes

from PIL import ImageGrab, Image

from src.core.domain.captured_image import CapturedWindow
from src.core.utils.windows_utils import get_window_info, careful_capture_window, capture_screen_region, write_windows_list


def _capture_windows(windows) -> List[CapturedWindow]:
    print(f"Found {len(windows)} windows to capture")

    # List to store all captured images
    captured_images = []

    # Capture each window and store in memory
    for i, window in enumerate(windows, 1):
        hwnd = window['hwnd']
        title = window['title']
        process = window['process']
        rect = window['rect']
        width = window['width']
        height = window['height']

        print(f"Capturing window {i}/{len(windows)}: {title} ({process})")

        # Create filename
        safe_title = "".join([c if c.isalnum() else "_" for c in title])[:50]
        safe_process = "".join([c if c.isalnum() else "_" for c in process])[:20]
        filename = f"{i:02d}_{safe_process}_{safe_title}.png"

        # First try using PrintWindow method (ignores overlapping)
        img = careful_capture_window(hwnd, width, height)
        capture_method = "PrintWindow (no overlap)"

        # If that fails, fall back to screen region capture
        if img is None:
            print("  Using fallback method: screen region capture")
            img = capture_screen_region(rect)
            capture_method = "Screen region (with overlap)"

        if img:
            captured_image = CapturedWindow(
                image=img,
                filename=filename,
                window_name=title,
                description=f"{title} ({process}) - {capture_method}"
            )
            captured_images.append(captured_image)
            print(f"  ✓ Captured using {capture_method}")
        else:
            print(f"  ✗ Failed to capture")

    return captured_images


def get_poker_window_info(poker_window_name):
    original_windows_info = get_window_info()
    windows = [w for w in original_windows_info if poker_window_name in w['title']]
    return windows


def save_images(
        captured_images: List[CapturedWindow],
        timestamp_folder: str = None
):
    print(f"\nSaving {len(captured_images)} captured images...")
    successes = 0

    print(f"Screenshots will be saved to: {timestamp_folder}")

    for i, captured_image in enumerate(captured_images, 1):
        try:
            filepath = os.path.join(timestamp_folder, captured_image.filename)
            if captured_image.save(filepath):
                print(f"  ✓ Saved {i}/{len(captured_images)}: {captured_image.filename}")
                successes += 1
            else:
                print(f"  ✗ Failed to save {captured_image.filename}")
        except Exception as e:
            print(f"  ✗ Failed to save {captured_image.filename}: {e}")

    # Print summary
    print("\n---- Capture Summary ----")
    print(f"Images captured in memory: {len(captured_images)}")
    print(f"Successfully saved to disk: {successes}")
    print(f"Screenshots saved to: {timestamp_folder}")
    print("Screenshot process completed.")


def _load_images_from_folder(timestamp_folder: str) -> List[CapturedWindow]:
    captured_images = []

    if not os.path.exists(timestamp_folder):
        print(f"❌ Debug folder not found: {timestamp_folder}")
        return captured_images

    # Get all image files in the folder
    image_extensions = ('.png')
    image_files = [f for f in os.listdir(timestamp_folder)
                   if f.lower().endswith(image_extensions) and not f.lower().endswith('_result.png')
                   and not f.lower() == 'full_screen.png']

    print(f"🔍 Loading {len(image_files)} images from debug folder: {timestamp_folder}")

    for filename in sorted(image_files):
        try:
            filepath = os.path.join(timestamp_folder, filename)
            image = Image.open(filepath)

            window_name = filename.replace('.png', '')  # Use full filename without extension

            captured_image = CapturedWindow(
                image=image,
                filename=filename,
                window_name=window_name,
                description="Loaded from debug folder"
            )
            captured_images.append(captured_image)
            print(f"  ✓ Loaded: {filename} → window: {window_name}")

        except Exception as e:
            print(f"  ❌ Failed to load {filename}: {str(e)}")

    return captured_images


def capture_and_save_windows(timestamp_folder: str = None, save_windows=True, debug=False) -> List[CapturedWindow]:
    if debug:
        # Debug mode: load images from existing folder
        captured_images = _load_images_from_folder(timestamp_folder)
        if captured_images:
            print(f"✅ Loaded {len(captured_images)} images from debug folder")
        else:
            print("❌ No images loaded from debug folder")
        return captured_images

    # Try to enable DPI awareness
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except:
        ctypes.windll.user32.SetProcessDPIAware()

    # Normal mode: capture windows

    # Get all window info
    windows = get_poker_window_info("Pot Limit Omaha")
    print(f"Found {len(windows)} poker windows with titles:")
    if len(windows) > 0:
        os.makedirs(timestamp_folder, exist_ok=True)
    else:
        return []

    captured_images = _capture_windows(windows=windows)

    # Save windows with the same timestamp
    if save_windows:
        try:
            full_screen = ImageGrab.grab()
            full_screen_captured = CapturedWindow(
                image=full_screen,
                filename="full_screen.png",
                window_name='full_screen',
                description="Full screen"
            )
            captured_images.append(full_screen_captured)
            print(f"Captured full screen")
        except Exception as e:
            print(f"Error capturing full screen: {e}")

        # Write the window list to windows.txt
        write_windows_list(windows, timestamp_folder)
        save_images(captured_images, timestamp_folder)

        # Remove full screen from the list before returning
        captured_images = [img for img in captured_images if img.window_name != 'full_screen']

    return captured_images