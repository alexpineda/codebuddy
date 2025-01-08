import os
from datetime import datetime
# from context import ContextHandler

class SessionManager:
    def __init__(self):
        self.sessions_dir = "sessions"
        self.current_session = None
        self.screenshots_dir = None
        self.trace_log_file = None
        
        # Create sessions directory if it doesn't exist
        os.makedirs(self.sessions_dir, exist_ok=True)
    
    def create_new_session(self):
        """Create a new session with datetime-based ID"""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = os.path.join(self.sessions_dir, session_id)
        screenshots_dir = os.path.join(session_dir, "screenshots")
        trace_log_file = os.path.join(session_dir, "trace_log.txt")
        
        # Create necessary directories
        os.makedirs(session_dir, exist_ok=True)
        os.makedirs(screenshots_dir, exist_ok=True)
        
        self.current_session = session_id
        self.screenshots_dir = screenshots_dir
        self.trace_log_file = trace_log_file
        
        # Add after creating session directory
        # context_handler = ContextHandler(session_dir)
        
        # Automatically detect and add git context if available
        # context_handler.add_git_context()
        
        # Add the session directory to context
        # context_handler.add_directory(session_dir)
        
        session_data = {
            'session_id': session_id,
            'session_dir': session_dir,
            'trace_log_file': trace_log_file,
            'screenshots_dir': screenshots_dir,
            # 'context_handler': context_handler  # Add context handler to session data
        }
        
        return session_data 