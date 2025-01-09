import sys
import time
import os
import select
import json
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint
from prompting import AppPrompts
from session import SessionManager
from threading import Event
import logging

console = Console()

class App:
    def __init__(self):
        with open('config.json') as f:
            config = json.load(f)

        self.config = config
        self.logger = logging.getLogger('HandlerManager')
        self.capture_interval = config.get('capture_interval', 15)
        self.app_prompts = AppPrompts(config)
        self.session = SessionManager(config)
        self.user_input_queue = []
        self.input_ready = Event()
        
    def initialize_session(self, previous_session=None):
        """Initialize or continue a session"""
        try:
            if previous_session:
                try:
                    self.session.create_new_session(continue_from=previous_session)
                    self.logger.debug(f"Successfully continued from previous session. New session ID: {self.session.current_session['session_id']}")
                    console.print("[green]✓[/] Continuing from previous session")
                except Exception as e:
                    self.session.create_new_session()
                    console.print("[red]Failed to continue from previous session. Starting new session.[/]")
            else:
                self.session.create_new_session()
        except Exception as e:
            self.logger.error(f"Error initializing session: {str(e)}", exc_info=True)
            raise
            
    def start_handlers(self):
        """Start the capture handler and input thread"""
        self.session.captures.start()

        
    def _check_for_input(self):
        """Check for user input"""
        while True:
            try:
                if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
                    line = sys.stdin.readline()
                    if line.strip() == '':  # Enter key was pressed
                        self.session.captures.pause()
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
                    self.session.captures.resume()
                    console.print("[green]✓[/] Resuming screen capture...")
                    return
                    
                if user_input.lower() == 'reset':
                    self.initialize_session()
                    
                    os.system('cls' if os.name == 'nt' else 'clear')
                    console.print(f"[green]✓[/] Log cleared and new session created {self.session.current_session['session_id']}")
                    console.print("[green]✓[/] Resuming screen capture...")
                    return
                elif user_input.lower() == 'continue':
                    self.session.captures.resume()
                    console.print("[green]✓[/] Resuming screen capture...")
                    return
                elif user_input.lower() == 'exit':
                    console.print("[red]Exiting...[/]")
                    os._exit(0)
                else:
                    with console.status("[bold green]Thinking...[/]", spinner="dots"):
                        assistant_response = self.session.prompts.handle_user_inquiry(user_input)
                    
                    console.print(Panel(
                        Text(assistant_response, style="bold blue"),
                        title="CodeBuddy's Response",
                        border_style="blue"
                    ))
            except (EOFError, KeyboardInterrupt):
                console.print("\n[yellow]Input interrupted. Type 'exit' to quit or 'continue' to resume capture.[/]")
                continue