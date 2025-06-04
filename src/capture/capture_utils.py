from PIL import ImageGrab

from src.capture.windows_utils import get_window_info, careful_capture_window, capture_screen_region


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
