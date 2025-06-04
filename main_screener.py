import os
import time
from datetime import datetime
from PIL import ImageGrab
import ctypes

from src.capture.windows_utils import careful_capture_window, capture_screen_region, get_window_info, write_windows_list
from src.utils.benchmark_utils import benchmark

# Try to enable DPI awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    ctypes.windll.user32.SetProcessDPIAware()


@benchmark
def main():
    # Create timestamped output folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_folder = os.path.join(current_dir, f"Dropbox/data_screenshots/_{timestamp}")
    os.makedirs(output_folder, exist_ok=True)

    print(f"Screenshots will be saved to: {output_folder}")

    # Get all window info
    windows = get_window_info()
    print(f"Found {len(windows)} windows to capture")

    # Write the window list to windows.txt
    write_windows_list(windows, output_folder)

    # First, capture the full screen
    try:
        full_screen = ImageGrab.grab()
        full_screen_path = os.path.join(output_folder, "full_screen.png")
        full_screen.save(full_screen_path)
        print(f"Saved full screen to {full_screen_path}")
    except Exception as e:
        print(f"Error capturing full screen: {e}")
        full_screen = None

    # Capture each window
    successes = 0

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
        filepath = os.path.join(output_folder, filename)

        # First try using PrintWindow method (ignores overlapping)
        img = careful_capture_window(hwnd, width, height)
        capture_method = "PrintWindow (no overlap)"

        # If that fails, fall back to screen region capture
        if img is None and full_screen is not None:
            print("  Using fallback method: screen region capture")
            img = capture_screen_region(rect)
            capture_method = "Screen region (with overlap)"

        if img:
            # Save the image
            img.save(filepath)
            print(f"  ✓ Saved using {capture_method}")
            successes += 1
        else:
            print(f"  ✗ Failed to capture")

    # Print summary
    print("\n---- Capture Summary ----")
    print(f"Total windows found: {len(windows)}")
    print(f"Successfully captured: {successes}")
    print(f"Screenshots saved to: {output_folder}")

    # We won't wait for a keypress as requested
    print("Screenshot process completed.")


if __name__ == "__main__":
    print("Reliable Window Screenshot Tool")
    print("------------------------------")

    try:
        while True:
            main()
            print("Sleep for 3 second...")
            time.sleep(3)
    except Exception as e:
        print(f"An error occurred: {e}")