import os
import threading
import time

from dotenv import load_dotenv
from utils import capture_and_save_screenshot, get_active_window_title, get_active_window_id
from rich.console import Console

load_dotenv()
is_debug = os.getenv("DEBUG") == "TRUE"
print(f"is_debug: {is_debug}")
print(f"DEBUG: {os.getenv('DEBUG')}")
class SessionCaptures:
    def __init__(self, session):
        self.session = session
        self.interval = session.config.get('capture_interval', 15)
        self.screenshot_counter = 0
        self.paused = False
        self.capture_thread = None
        self.starting_window_id = None
        self.console = Console()
        self._set_starting_window()

    @property
    def session_prompts(self):
        return self.session.prompts

    @property
    def screenshots_dir(self):
        return self.session.current_session["screenshots_dir"]

    def _set_starting_window(self):
        self.starting_window_id = get_active_window_id()

    def capture_screen(self):
        # Skip capture if we're in the starting window
        if not is_debug and get_active_window_id() == self.starting_window_id:
            self.console.print("[yellow]Skipping capture[/], still in starting window")
            return

        active_window_title = get_active_window_title()
        self.console.print(f"[green]📸 Capturing screen[/] {active_window_title}")
        filename, base64_image = capture_and_save_screenshot(
            self.screenshot_counter, 
            screenshots_dir=self.screenshots_dir
        )
        self.screenshot_counter += 1

        self.session_prompts.process_screenshot(base64_image, filename, active_window_title)

    def capture_loop(self):
        while True:
            time.sleep(self.interval)
            if not self.paused:
                self.capture_screen()

    def start(self):
        self.capture_thread = threading.Thread(target=self.capture_loop)
        self.capture_thread.daemon = True
        self.capture_thread.start()

    def stop(self):
        self.capture_thread.join()

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False 