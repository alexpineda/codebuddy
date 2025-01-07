import threading
import time
from utils import capture_and_save_screenshot, get_active_window_title, get_active_window_id
from rich.console import Console

class CaptureHandler:
    def __init__(self, prompt_handler, interval=15, screenshots_dir="screenshots"):
        self.prompt_handler = prompt_handler
        self.interval = interval
        self.screenshot_counter = 0
        self.paused = False
        self.capture_thread = None
        self.starting_window_id = None
        self.screenshots_dir = screenshots_dir
        self.console = Console()

    def set_starting_window(self):
        self.starting_window_id = get_active_window_id()

    def capture_screen(self):
        # Skip capture if we're in the starting window
        if get_active_window_id() == self.starting_window_id:
            self.console.print("[yellow]Skipping capture[/], still in starting window")
            return

        active_window_title = get_active_window_title()
        self.console.print(f"[green]📸 Capturing screen[/] {active_window_title}")
        filename, base64_image = capture_and_save_screenshot(
            self.screenshot_counter, 
            screenshots_dir=self.screenshots_dir
        )
        self.screenshot_counter += 1

        self.prompt_handler.process_screenshot(base64_image, filename, active_window_title)

    def capture_loop(self):
        while True:
            time.sleep(self.interval)
            if not self.paused:
                self.capture_screen()

    def start(self):
        self.capture_thread = threading.Thread(target=self.capture_loop)
        self.capture_thread.daemon = True
        self.capture_thread.start()

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False 