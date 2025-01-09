import os
from datetime import datetime
import logging
# from context import ContextHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class SessionManager:
    def __init__(self):
        self.sessions_dir = "sessions"
        self.current_session = None
        self.screenshots_dir = None
        self.trace_log_file = None
        self.logger = logging.getLogger('SessionManager')
        
        # Create sessions directory if it doesn't exist
        os.makedirs(self.sessions_dir, exist_ok=True)
        self.logger.info(f"Initialized SessionManager with sessions directory: {self.sessions_dir}")
    
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
                'trace_log_file': os.path.join(self.sessions_dir, most_recent, "trace_log.txt"),
                'screenshots_dir': os.path.join(self.sessions_dir, most_recent, "screenshots")
            }
            
            # Verify the trace log file exists
            if not os.path.exists(session_data['trace_log_file']):
                self.logger.warning(f"Trace log file not found in recent session: {session_data['trace_log_file']}")
            
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
            trace_log_file = os.path.join(session_dir, "trace_log.txt")
            
            self.logger.info(f"Creating new session with ID: {session_id}")
            
            # Create necessary directories
            os.makedirs(session_dir, exist_ok=True)
            os.makedirs(screenshots_dir, exist_ok=True)
            self.logger.info(f"Created session directories: {session_dir}")
            
            # If continuing from previous session, copy the trace log
            if continue_from:
                self.logger.info(f"Attempting to continue from previous session: {continue_from['session_id']}")
                if os.path.exists(continue_from['trace_log_file']):
                    import shutil
                    shutil.copy2(continue_from['trace_log_file'], trace_log_file)
                    self.logger.info(f"Copied trace log from previous session: {continue_from['trace_log_file']} -> {trace_log_file}")
                else:
                    self.logger.warning(f"Previous session trace log not found: {continue_from['trace_log_file']}")
            
            self.current_session = session_id
            self.screenshots_dir = screenshots_dir
            self.trace_log_file = trace_log_file
            
            session_data = {
                'session_id': session_id,
                'session_dir': session_dir,
                'trace_log_file': trace_log_file,
                'screenshots_dir': screenshots_dir,
            }
            
            self.logger.info(f"Successfully created new session: {session_id}")
            return session_data
            
        except Exception as e:
            self.logger.error(f"Error creating new session: {str(e)}", exc_info=True)
            raise 