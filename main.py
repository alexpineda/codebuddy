import sys
import threading
import time
import os
import select
import json
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from app import App
from prompting import AppPrompts
import logging
from utils import append_log

load_dotenv()

# Initialize logging
logging_level = logging.DEBUG if os.getenv('DEBUG', '').upper() == 'TRUE' else logging.WARNING
logging.basicConfig(
    level=logging_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('main')

# Initialize Rich console
console = Console()

if __name__ == "__main__":
    # Display welcome message and session options
    welcome_text = """
🤖 Welcome to CodeBuddy! 

I'll record your screen periodically and you can ask questions as you work.
Press Enter at any time to pause and enter inquiry mode.
Screen capture is automatically paused when you return to this window.
    """
    console.print(Panel(welcome_text, title="CodeBuddy", style="bold green"))
    
    # Initialize app
    app = App()
    
    previous_session = app.session.get_most_recent_session()
    if previous_session:
        previous_session_log = open(previous_session['session_log_filepath'], 'r').read()
        previous_session_description = app.app_prompts.prompt(f"In as few words as possible, describe the previous productivity session. Speak to the user as if you were a human assistant. Log: {previous_session_log}")
        console.print(f"[bold blue]Previously on CodeBuddy:[/] {previous_session_description}")
        continue_previous = console.input("\n[blue]Would you like to continue from previous session? (y/N): ").lower().strip()
    else:
        continue_previous = 'n'
   
    if continue_previous == 'n':
        previous_session = None
        # Ask for initial objective
        initial_objective = console.input("\n[yellow]What's your objective for this session? (Press Enter to skip): ").strip()
        if initial_objective:
            append_log(f"Initial objective (if any): {initial_objective}", app.session_log_filepath)
        
    with console.status("[bold yellow]Initializing...[/]", spinner="dots"):
        app.initialize_session(previous_session)

    
    # Start the handlers
    input_thread = threading.Thread(target=app._check_for_input)
    input_thread.daemon = True
    input_thread.start()

    console.print(f"[bold green]Session started {app.session.current_session['session_id']}, capturing every {app.capture_interval} seconds[/]")

    try:
        while True:
            if app.user_input_queue:
                action = app.user_input_queue.pop(0)
                if action == "inquiry":
                    console.print("\n[bold green]Entering inquiry mode. Screen capture paused.[/]")
                    app.prompt_user()  # Use the handler_manager's prompt_user method
                    # Start a new input checking thread after returning from prompt_user
                    input_thread = threading.Thread(target=app._check_for_input)
                    input_thread.daemon = True
                    input_thread.start()
            time.sleep(0.1)
    except KeyboardInterrupt:
        console.print("\n[red]Exiting...[/]")
        os._exit(0)
