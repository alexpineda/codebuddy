import os
from datetime import datetime
import logging

from capture import SessionCaptures
from prompting import SessionPrompts
# from context import ContextHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO if os.getenv('DEBUG', '').upper() == 'TRUE' else logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class SessionManager:
    def __init__(self, config):
        self.config = config
        self.sessions_dir = config.get("session_dir", "sessions")

        self.current_session = None
        self.logger = logging.getLogger('SessionManager')

        self.prompts = None 
        self.captures = None

        # Create sessions directory if it doesn't exist
        os.makedirs(self.sessions_dir, exist_ok=True)
        self.logger.info(f"Initialized SessionManager with sessions directory: {self.sessions_dir}")
    
    def write_to_log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.current_session['session_log_filepath'], 'a') as log_file:
            log_file.write(f"[{timestamp}] {message}\n")

    def get_most_recent_session(self):
        """Get the most recent session directory"""
        try:
            self.logger.info("Attempting to find most recent session")
            sessions = [d for d in os.listdir(self.sessions_dir) 
                       if os.path.isdir(os.path.join(self.sessions_dir, d))]
            
            if not sessions:
                self.logger.info("No previous sessions found")
                return None
            
            # Sort sessions by name (which is datetime-based) to get the most recent
            sessions.sort(reverse=True)
            most_recent = sessions[0]
            self.logger.info(f"Found most recent session: {most_recent}")
            
            session_data = {
                'session_id': most_recent,
                'session_dir': os.path.join(self.sessions_dir, most_recent),
                'session_log_filepath': os.path.join(self.sessions_dir, most_recent, "trace_log.txt"),
                'screenshots_dir': os.path.join(self.sessions_dir, most_recent, "screenshots")
            }
            
            # Verify the trace log file exists
            if not os.path.exists(session_data['session_log_filepath']):
                self.logger.warning(f"Trace log file not found in recent session: {session_data['session_log_filepath']}")
                raise Exception(f"Trace log file not found in recent session: {session_data['session_log_filepath']}")

            # Verify contents of trace log file are not empty
            if os.path.getsize(session_data['session_log_filepath']) == 0:
                self.logger.warning(f"Trace log file is empty: {session_data['session_log_filepath']}")
                raise Exception(f"Trace log file is empty: {session_data['session_log_filepath']}")

            return session_data
        except Exception as e:
            self.logger.error(f"Error getting most recent session: {str(e)}", exc_info=True)
            return None
    
    def create_new_session(self, continue_from=None):
        """Create a new session with datetime-based ID"""
        try:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_dir = os.path.join(self.sessions_dir, session_id)
            screenshots_dir = os.path.join(session_dir, "screenshots")
            session_log_filepath = os.path.join(session_dir, "trace_log.txt")
            
            self.logger.debug(f"Creating new session with ID: {session_id}")
            
            # Create necessary directories
            os.makedirs(session_dir, exist_ok=True)
            os.makedirs(screenshots_dir, exist_ok=True)
            # Create trace log file
            with open(session_log_filepath, 'w') as log_file:
                log_file.write("")
            self.logger.debug(f"Created session directories: {session_dir}")
            
            # If continuing from previous session, copy the trace log
            if continue_from:
                self.logger.debug(f"Attempting to continue from previous session: {continue_from['session_id']}")
                if os.path.exists(continue_from['session_log_filepath']):
                    import shutil
                    shutil.copy2(continue_from['session_log_filepath'], session_log_filepath)
                    self.logger.debug(f"Copied trace log from previous session: {continue_from['session_log_filepath']} -> {session_log_filepath}")
                else:
                    self.logger.warning(f"Previous session trace log not found: {continue_from['session_log_filepath']}")
            
            self.current_session = {
                'session_id': session_id,
                'session_dir': session_dir,
                'session_log_filepath': session_log_filepath,
                'screenshots_dir': screenshots_dir,
            }

            self.prompts = SessionPrompts(self)
            self.captures = SessionCaptures(self)
            self.captures.start()
            
            self.logger.debug(f"Successfully created new session: {session_id}")
            
        except Exception as e:
            self.logger.error(f"Error creating new session: {str(e)}", exc_info=True)
            raise 