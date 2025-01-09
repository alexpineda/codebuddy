import sys
import threading
import time
import os
import select
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import track
from rich import print as rprint
from prompting import PromptHandler
from capture import CaptureHandler
from session import SessionManager
from threading import Event
import logging
from utils import log_trace

load_dotenv()

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('main')

class HandlerManager:
    def __init__(self, capture_interval):
        self.logger = logging.getLogger('HandlerManager')
        self.capture_interval = capture_interval
        self.session_manager = SessionManager()
        self.session = None
        self._trace_log_file = None
        self._screenshots_dir = None
        self.user_input_queue = []
        self.input_ready = Event()
        self.prompt_handler = None
        self.capture_handler = None
        
    @property
    def trace_log_file(self):
        return self._trace_log_file
        
    @property
    def screenshots_dir(self):
        return self._screenshots_dir
        
    def initialize_session(self, continue_previous=False):
        """Initialize or continue a session"""
        try:
            if continue_previous:
                self.logger.info("Attempting to get most recent session")
                previous_session = self.session_manager.get_most_recent_session()
                if previous_session:
                    self.logger.info(f"Found previous session: {previous_session['session_id']}")
                    try:
                        self.session = self.session_manager.create_new_session(continue_from=previous_session)
                        self._trace_log_file = self.session['trace_log_file']
                        self._screenshots_dir = self.session['screenshots_dir']
                        self.logger.info(f"Successfully continued from previous session. New session ID: {self.session['session_id']}")
                        return True, "[green]✓[/] Continuing from previous session"
                    except Exception as e:
                        self.logger.error(f"Failed to continue from previous session: {str(e)}", exc_info=True)
                        self._create_new_session()
                        return False, "[red]Failed to continue from previous session. Starting new session.[/]"
                else:
                    self.logger.warning("No previous session found")
                    self._create_new_session()
                    return False, "[yellow]No previous session found. Starting new session.[/]"
            else:
                self._create_new_session()
                return True, None
        except Exception as e:
            self.logger.error(f"Error initializing session: {str(e)}", exc_info=True)
            raise
            
    def _create_new_session(self):
        """Create a new session"""
        self.session = self.session_manager.create_new_session()
        self._trace_log_file = self.session['trace_log_file']
        self._screenshots_dir = self.session['screenshots_dir']
        
    def initialize_handlers(self):
        """Initialize prompt and capture handlers"""
        self.prompt_handler = PromptHandler(self.trace_log_file, self.capture_interval)
        self.capture_handler = CaptureHandler(self.prompt_handler, self.capture_interval, screenshots_dir=self.screenshots_dir)
        self.capture_handler.set_starting_window()
        self.logger.info(f"Session started {self.session['session_id']}")
        
    def start_handlers(self):
        """Start the capture handler and input thread"""
        self.capture_handler.start()
        input_thread = threading.Thread(target=self._check_for_input)
        input_thread.daemon = True
        input_thread.start()
        
    def _check_for_input(self):
        """Check for user input"""
        while True:
            try:
                if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
                    line = sys.stdin.readline()
                    if line.strip() == '':  # Enter key was pressed
                        self.capture_handler.pause()
                        self.user_input_queue.append("inquiry")
                        break
            except (select.error, IOError) as e:
                self.logger.error(f"Input error: {e}")
                time.sleep(0.1)
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                time.sleep(0.1)
        
    def prompt_user(self):
        """Handle user prompts and commands"""
        while True:
            try:
                user_input = console.input("\n[bold green]Enter your question[/] ([dim]'exit' to quit, 'reset' to clear, 'continue' to resume[/]): ")
                
                if not user_input:
                    self.capture_handler.resume()
                    console.print("[green]✓[/] Resuming screen capture...")
                    return
                    
                if user_input.lower() == 'reset':
                    self.session = self.session_manager.create_new_session()
                    self._trace_log_file = self.session['trace_log_file']
                    self._screenshots_dir = self.session['screenshots_dir']
                    
                    self.prompt_handler.log_file = self.trace_log_file
                    self.capture_handler.screenshots_dir = self.screenshots_dir
                    
                    os.system('cls' if os.name == 'nt' else 'clear')
                    console.print(f"[green]✓[/] Log cleared and new session created {self.session['session_id']}")
                    self.capture_handler.resume()
                    console.print("[green]✓[/] Resuming screen capture...")
                    return
                elif user_input.lower() == 'continue':
                    self.capture_handler.resume()
                    console.print("[green]✓[/] Resuming screen capture...")
                    return
                elif user_input.lower() == 'exit':
                    console.print("[red]Exiting...[/]")
                    os._exit(0)
                else:
                    with console.status("[bold green]Thinking...[/]", spinner="dots"):
                        assistant_response = self.prompt_handler.handle_user_inquiry(user_input)
                    
                    console.print(Panel(
                        Text(assistant_response, style="bold blue"),
                        title="CodeBuddy's Response",
                        border_style="blue"
                    ))
            except (EOFError, KeyboardInterrupt):
                console.print("\n[yellow]Input interrupted. Type 'exit' to quit or 'continue' to resume capture.[/]")
                continue

# Initialize Rich console
console = Console()

DEFAULT_CAPTURE_INTERVAL = 5

# Get capture interval from command line argument or use default
if len(sys.argv) > 1:
    try:
        CAPTURE_INTERVAL = float(sys.argv[1])
    except ValueError:
        console.print(f"[yellow]Invalid interval provided. Using default: {DEFAULT_CAPTURE_INTERVAL} seconds[/]")
        CAPTURE_INTERVAL = DEFAULT_CAPTURE_INTERVAL
else:
    console.print(f"[dim]No interval provided. Using default: {DEFAULT_CAPTURE_INTERVAL} seconds[/]")
    CAPTURE_INTERVAL = DEFAULT_CAPTURE_INTERVAL

if __name__ == "__main__":
    # Display welcome message and session options
    welcome_text = """
🤖 Welcome to CodeBuddy! 

I'll record your screen periodically and you can ask questions as you work.
Press Enter at any time to pause and enter inquiry mode.
Screen capture is automatically paused when you return to this window.
    """
    console.print(Panel(welcome_text, title="CodeBuddy", style="bold green"))
    
    # Ask for initial objective
    initial_objective = console.input("\nWhat's your objective for this session? (Press Enter to skip): ").strip()
    
    # Initialize handler manager
    handler_manager = HandlerManager(CAPTURE_INTERVAL)
    
    # Ask user if they want to continue from previous session
    continue_previous = console.input("\nWould you like to continue from previous session? (y/N): ").lower().strip()
    logger.info(f"User chose to {'continue from previous session' if continue_previous == 'y' else 'start new session'}")
    
    # Initialize session and handlers
    with console.status("[bold green]Initializing...[/]", spinner="dots"):
        success, message = handler_manager.initialize_session(continue_previous == 'y')
        if message:
            console.print(message)
            
        handler_manager.initialize_handlers()
        
        # Log initial objective if provided
        if initial_objective:
            log_trace(f"Initial objective (if any): {initial_objective}", handler_manager.trace_log_file)
    
    # Start the handlers
    handler_manager.start_handlers()
    print(f"Session started {handler_manager.session['session_id']}, capturing every {CAPTURE_INTERVAL} seconds")

    try:
        while True:
            if handler_manager.user_input_queue:
                action = handler_manager.user_input_queue.pop(0)
                if action == "inquiry":
                    console.print("\n[bold green]Entering inquiry mode. Screen capture paused.[/]")
                    handler_manager.prompt_user()  # Use the handler_manager's prompt_user method
                    # Start a new input checking thread after returning from prompt_user
                    input_thread = threading.Thread(target=handler_manager._check_for_input)
                    input_thread.daemon = True
                    input_thread.start()
            time.sleep(0.1)
    except KeyboardInterrupt:
        console.print("\n[red]Exiting...[/]")
        os._exit(0)
