import time
import ctypes

from src.capture.capture_utils import capture_windows, save_windows
from src.utils.benchmark_utils import benchmark

# Try to enable DPI awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    ctypes.windll.user32.SetProcessDPIAware()


@benchmark
def main():
    captured_images, windows = capture_windows()

    save_windows(captured_images, windows)


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