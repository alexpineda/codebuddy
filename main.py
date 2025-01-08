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

load_dotenv()

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

# Initialize session manager and create first session
session_manager = SessionManager()
session = session_manager.create_new_session()
TRACE_LOG_FILE = session['trace_log_file']
SCREENSHOTS_DIR = session['screenshots_dir']

user_input_queue = []
prompt_handler = PromptHandler(TRACE_LOG_FILE, CAPTURE_INTERVAL)
capture_handler = CaptureHandler(prompt_handler, CAPTURE_INTERVAL, screenshots_dir=SCREENSHOTS_DIR)

# Add near the top with other global variables
input_ready = Event()
context_handler = None

def prompt_user():
    while True:
        try:
            # Remove the input_ready event check since we're already in the prompt loop
            user_input = console.input("\n[bold green]Enter your question[/] ([dim]'exit' to quit, 'reset' to clear, 'continue' to resume[/]): ")
            
            if not user_input:
                capture_handler.resume()
                console.print("[green]✓[/] Resuming screen capture...")
                return
                
            if user_input.lower() == 'reset':
                session = session_manager.create_new_session()
                global TRACE_LOG_FILE, SCREENSHOTS_DIR
                TRACE_LOG_FILE = session['trace_log_file']
                SCREENSHOTS_DIR = session['screenshots_dir']
                
                prompt_handler.log_file = TRACE_LOG_FILE
                capture_handler.screenshots_dir = SCREENSHOTS_DIR
                
                os.system('cls' if os.name == 'nt' else 'clear')
                console.print(f"[green]✓[/] Log cleared and new session created {session['session_id']}")
                capture_handler.resume()
                console.print("[green]✓[/] Resuming screen capture...")
                return
            elif user_input.lower() == 'continue':
                capture_handler.resume()
                console.print("[green]✓[/] Resuming screen capture...")
                return  # Exit the prompt loop when continuing
            elif user_input.lower() == 'exit':
                console.print("[red]Exiting...[/]")
                os._exit(0)
            else:
                with console.status("[bold green]Thinking...[/]", spinner="dots"):
                    assistant_response = prompt_handler.handle_user_inquiry(user_input)
                
                console.print(Panel(
                    Text(assistant_response, style="bold blue"),
                    title="CodeBuddy's Response",
                    border_style="blue"
                ))
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]Input interrupted. Type 'exit' to quit or 'continue' to resume capture.[/]")
            continue

def check_for_input():
    while True:
        try:
            # Simplified input checking that just looks for Enter key
            if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
                line = sys.stdin.readline()
                if line.strip() == '':  # Enter key was pressed
                    capture_handler.pause()
                    user_input_queue.append("inquiry")
                    break  # Exit the loop after getting input
        except (select.error, IOError) as e:
            console.print(f"[red]Input error: {e}[/]")
            time.sleep(0.1)
        except Exception as e:
            console.print(f"[red]Unexpected error: {e}[/]")
            time.sleep(0.1)

if __name__ == "__main__":
    # Display welcome message
    welcome_text = """
🤖 Welcome to CodeBuddy! 

I'll record your screen periodically and you can ask questions as you work.
Press Enter at any time to pause and enter inquiry mode.
Screen capture is automatically paused when you return to this window.
    """
    console.print(Panel(welcome_text, title="CodeBuddy", style="bold green"))
    console.print(f"\n[cyan]Screen capture interval:[/] {CAPTURE_INTERVAL} seconds")
    
    # Set the starting window before beginning capture
    with console.status("[bold green]Initializing...[/]", spinner="dots"):
        capture_handler.set_starting_window()
        print(f"Session started {session['session_id']}")

    # Start the capture handler
    capture_handler.start()

    # Start the input checking thread
    input_thread = threading.Thread(target=check_for_input)
    input_thread.daemon = True
    input_thread.start()

    # After session initialization
    # context_handler = session['context_handler']

    try:
        while True:
            if user_input_queue:
                action = user_input_queue.pop(0)
                if action == "inquiry":
                    console.print("\n[bold green]Entering inquiry mode. Screen capture paused.[/]")
                    prompt_user()  # Enter prompt mode
                    # Start a new input checking thread after returning from prompt_user
                    input_thread = threading.Thread(target=check_for_input)
                    input_thread.daemon = True
                    input_thread.start()
            time.sleep(0.1)
    except KeyboardInterrupt:
        console.print("\n[red]Exiting...[/]")
        os._exit(0)
