from typing import Dict, List, Optional
import re
import os
from dataclasses import dataclass

@dataclass
class ContextSuggestion:
    file_path: Optional[str] = None
    confidence: float = 0.0
    last_seen: float = 0.0
    
class SuggestedContextFinder:
    def __init__(self):
        self.root_dir = os.getcwd()  # Get the project root directory
        
    def extract_file_paths(self, text: str) -> List[str]:
        """Extract potential file paths from text."""
        # Match common file patterns
        file_patterns = [
            r'(?:^|\s)([\/\w-]+\.[a-zA-Z0-9]+)',  # Basic file with any extension
            r'(?:^|\s)((?:\.{1,2}\/)?(?:[\w-]+\/)*[\w-]+\.[a-zA-Z0-9]+)', # Paths with directories
            r'(?:^|\s)([A-Z]:[\\/](?:[\w-]+[\\/])*[\w-]+\.[a-zA-Z0-9]+)', # Windows paths
            r'(?:^|\s)((?:[\w-]+\/)*[\w-]+\.[a-zA-Z0-9]+)' # Simple relative paths
        ]
        
        paths = []
        for pattern in file_patterns:
            matches = re.finditer(pattern, text)
            paths.extend(match.group(1) for match in matches)
            
        # Remove duplicates while preserving order
        unique_paths = list(dict.fromkeys(paths))
        
        # Verify files exist and convert to absolute paths
        verified_paths = []
        for path in unique_paths:
            # Try different path combinations
            possible_paths = [
                path,  # As is
                os.path.join(self.root_dir, path),  # From root
                os.path.abspath(path),  # Absolute
                os.path.normpath(path)  # Normalized
            ]
            
            for possible_path in possible_paths:
                if os.path.isfile(possible_path):
                    verified_paths.append(possible_path)
                    break
                    
        return verified_paths

    def analyze_log(self, log_file: str, recent_lines: int = 50) -> ContextSuggestion:
        """Analyze the trace log to find the most likely current context."""
        if not os.path.exists(log_file):
            return ContextSuggestion()
            
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                # Read last N lines for recent context
                lines = f.readlines()[-recent_lines:]
                text = ''.join(lines)
                
            files = self.extract_file_paths(text)
            context = ContextSuggestion()
            
            if files:
                context.file_path = files[-1]  # Most recent file
                # Higher confidence since we verified the file exists
                context.confidence = min(0.6 + (len(files) * 0.1), 0.9)
                
            return context
            
        except Exception as e:
            print(f"Error analyzing log: {e}")
            return ContextSuggestion()

    def get_suggested_context(self, log_file: str) -> Dict:
        """Get suggested context from the log file."""
        context = self.analyze_log(log_file)
        
        return {
            "file_path": context.file_path,
            "confidence": context.confidence
        } 