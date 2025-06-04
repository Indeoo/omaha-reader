import os
import time
from datetime import datetime
from PIL import ImageGrab
import ctypes

from src.capture.capture_utils import capture_windows
from src.capture.windows_utils import careful_capture_window, capture_screen_region, get_window_info, write_windows_list
from src.utils.benchmark_utils import benchmark

# Try to enable DPI awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    ctypes.windll.user32.SetProcessDPIAware()


@benchmark
def main():
    captured_images, windows = capture_windows()

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