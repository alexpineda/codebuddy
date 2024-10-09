import os
import io
import base64
import pyautogui
from PIL import Image
from datetime import datetime
import platform
import subprocess

SCREENSHOT_DIR = "screenshots"
MAX_IMAGE_SIZE = (2000, 768)

def capture_and_save_screenshot(screenshot_counter):
    # Create screenshots directory if it doesn't exist
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    # Capture the screenshot
    screenshot = pyautogui.screenshot()
    
    # Resize screenshot
    resized_screenshot = resize_image(screenshot)

    # Save screenshot to file
    filename = f"{SCREENSHOT_DIR}/screenshot_{screenshot_counter:04d}.png"
    resized_screenshot.save(filename)

    # Convert resized screenshot to base64
    img_byte_array = io.BytesIO()
    resized_screenshot.save(img_byte_array, format='PNG')
    base64_image = base64.b64encode(img_byte_array.getvalue()).decode('utf-8')

    return filename, base64_image

def resize_image(image):
    """Resize the image to fit within MAX_IMAGE_SIZE while maintaining aspect ratio."""
    image.thumbnail(MAX_IMAGE_SIZE, Image.LANCZOS)
    return image

def log_trace(message, log_file_path):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file_path, "a") as log_file:
        log_file.write(f"[{timestamp}] {message}\n")

def clear_log(log_file_path):
    with open(log_file_path, "w") as log_file:
        log_file.write("")

def get_active_window_title():
    system = platform.system()

    if system == "Darwin":  # macOS
        try:
            script = '''
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
                set windowTitle to ""
                tell process frontApp
                    if exists (1st window whose value of attribute "AXMain" is true) then
                        set windowTitle to name of 1st window whose value of attribute "AXMain" is true
                    end if
                end tell
                return {frontApp, windowTitle}
            end tell
            '''
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=True)
            app_name, window_title = result.stdout.strip().split(", ")
            return f"{app_name}: {window_title}" if window_title else app_name
        except subprocess.CalledProcessError:
            return "Unknown"

    elif system == "Windows":
        try:
            import win32gui
            window = win32gui.GetForegroundWindow()
            return win32gui.GetWindowText(window)
        except ImportError:
            return "win32gui not installed"
        except:
            return "Unknown"

    else:
        return f"Unsupported OS: {system}"