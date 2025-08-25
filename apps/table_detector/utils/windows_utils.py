import ctypes
import os
import sys
from datetime import datetime

from PIL import Image, ImageGrab
from loguru import logger


def careful_capture_window(hwnd, width, height):
    import win32gui
    import win32process
    import win32con
    import win32ui

    """Carefully capture a window using PrintWindow API with proper resource handling"""
    try:
        # Make sure dimensions are valid
        if width <= 0 or height <= 0:
            return None

        # Create device contexts
        hwndDC = None
        mfcDC = None
        saveDC = None
        saveBitMap = None
        result = None

        try:
            # 1. Get window DC
            hwndDC = win32gui.GetWindowDC(hwnd)

            # 2. Create compatible DC from handle
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)

            # 3. Create memory DC
            saveDC = mfcDC.CreateCompatibleDC()

            # 4. Create bitmap object
            saveBitMap = win32ui.CreateBitmap()

            # 5. Create compatible bitmap
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)

            # 6. Select bitmap into DC
            saveDC.SelectObject(saveBitMap)

            # 7. Use PrintWindow with PW_RENDERFULLCONTENT flag
            # We directly access the C function to avoid any potential issues
            PW_RENDERFULLCONTENT = 2
            result = ctypes.windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), PW_RENDERFULLCONTENT)

            # 8. If that fails, try standard PrintWindow
            if result == 0:
                result = ctypes.windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 0)

            # 9. If both PrintWindow attempts fail, create empty image
            if result == 0:
                return None

            # 10. Get bitmap info and bits
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)

            # 11. Create PIL Image
            img = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1)

            return img

        finally:
            # 12. Clean up resources in reverse order
            # Each cleanup is in its own try/except to ensure all resources are released
            if saveBitMap:
                try:
                    saveBitMap.DeleteObject()
                except:
                    pass

            if saveDC:
                try:
                    saveDC.DeleteDC()
                except:
                    pass

            if mfcDC:
                try:
                    mfcDC.DeleteDC()
                except:
                    pass

            if hwndDC:
                try:
                    win32gui.ReleaseDC(hwnd, hwndDC)
                except:
                    pass

    except Exception as e:
        logger.error(f"  Capture error: {e}")
        return None


def capture_screen_region(rect):
    """Capture a region of the screen using PIL as fallback"""
    try:
        with ImageGrab.grab() as screen:
            window_img = screen.crop(rect)
        return window_img
    except Exception as e:
        logger.error(f"  Error capturing screen region: {e}")
        return None


def get_window_info():
    import win32gui

    """Get info about all visible, non-minimized windows"""
    window_info = []

    def callback(hwnd, results):
        # Skip invisible or minimized windows
        if not win32gui.IsWindowVisible(hwnd) or win32gui.IsIconic(hwnd):
            return True

        # Get title and skip empty titles
        title = win32gui.GetWindowText(hwnd)
        if not title:
            return True

        # Get window rect and dimensions
        rect = win32gui.GetWindowRect(hwnd)
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]

        # Skip small windows
        if width < 50 or height < 50:
            return True

        # Get process name
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            import psutil
            process = psutil.Process(pid)
            process_name = process.name()
        except:
            process_name = "unknown"

        results.append({
            'hwnd': hwnd,
            'title': title,
            'rect': rect,
            'process': process_name,
            'width': width,
            'height': height
        })
        return True

    windows = []
    win32gui.EnumWindows(callback, windows)
    return windows


def write_windows_list(windows, output_folder):
    """Write the list of all windows to windows.txt"""
    windows_file_path = os.path.join(output_folder, "windows.txt")

    try:
        with open(windows_file_path, 'w', encoding='utf-8') as f:
            f.write(f"Window List - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")

            for i, window in enumerate(windows, 1):
                f.write(f"Window {i}:\n")
                f.write(f"  Title: {window['title']}\n")
                f.write(f"  Process: {window['process']}\n")
                f.write(f"  HWND: {window['hwnd']}\n")
                f.write(f"  Position: ({window['rect'][0]}, {window['rect'][1]})\n")
                f.write(f"  Size: {window['width']} x {window['height']}\n")
                f.write(f"  Rectangle: {window['rect']}\n")
                f.write("-" * 40 + "\n")

            f.write(f"\nTotal windows: {len(windows)}\n")

        #print(f"Window list written to: {windows_file_path}")

    except Exception as e:
        logger.error(f"Error writing windows list: {e}")


def initialize_platform():
    """Initialize platform-specific settings"""
    if sys.platform == "win32":
        _initialize_windows_dpi()

def _initialize_windows_dpi():
    """Set Windows DPI awareness once per process"""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        logger.info("✅ Windows DPI awareness set")
    except:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
            logger.info("✅ Windows DPI awareness set (fallback)")
        except:
            logger.warning("⚠️ Could not set DPI awareness")