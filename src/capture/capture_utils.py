import os
from datetime import datetime

from PIL import ImageGrab

from src.capture.windows_utils import get_window_info, careful_capture_window, capture_screen_region, write_windows_list


def capture_windows():
    # Get all window info
    windows = get_window_info()
    print(f"Found {len(windows)} windows to capture")
    # List to store all captured images with their metadata
    captured_images = []
    # First, capture the full screen
    try:
        full_screen = ImageGrab.grab()
        captured_images.append({
            'image': full_screen,
            'filename': "full_screen.png",
            'description': "Full screen"
        })
        print(f"Captured full screen")
    except Exception as e:
        print(f"Error capturing full screen: {e}")
        full_screen = None
    # Capture each window and store in memory
    for i, window in enumerate(windows, 1):
        hwnd = window['hwnd']
        title = window['title']
        process = window['process']
        rect = window['rect']
        width = window['width']
        height = window['height']

        print(f"Capturing window {i}/{len(windows)}: {title} ({process})")

        if "Lobby" not in title and "TableCover" not in title and "Pot Limit Omaha" not in title:
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
            print("  Using fallback method: screen region capture")
            img = capture_screen_region(rect)
            capture_method = "Screen region (with overlap)"

        if img:
            captured_images.append({
                'image': img,
                'filename': filename,
                'description': f"{title} ({process}) - {capture_method}"
            })
            print(f"  ✓ Captured using {capture_method}")
        else:
            print(f"  ✗ Failed to capture")
    return captured_images, windows


def save_windows(captured_images, windows):
    # Now save all captured images in a separate loop
    print(f"\nSaving {len(captured_images)} captured images...")
    successes = 0
    # Create timestamped output folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_folder = os.path.join(current_dir, f"Dropbox/data_screenshots/_{timestamp}")
    os.makedirs(output_folder, exist_ok=True)
    print(f"Screenshots will be saved to: {output_folder}")
    # Write the window list to windows.txt
    write_windows_list(windows, output_folder)
    for i, captured_item in enumerate(captured_images, 1):
        try:
            filepath = os.path.join(output_folder, captured_item['filename'])
            captured_item['image'].save(filepath)
            print(f"  ✓ Saved {i}/{len(captured_images)}: {captured_item['filename']}")
            successes += 1
        except Exception as e:
            print(f"  ✗ Failed to save {captured_item['filename']}: {e}")
    # Print summary
    print("\n---- Capture Summary ----")
    print(f"Total windows found: {len(windows)}")
    print(f"Images captured in memory: {len(captured_images)}")
    print(f"Successfully saved to disk: {successes}")
    print(f"Screenshots saved to: {output_folder}")
    # We won't wait for a keypress as requested
    print("Screenshot process completed.")