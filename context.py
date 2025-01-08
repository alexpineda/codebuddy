import os
import git
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
import json

@dataclass
class ContextItem:
    type: str
    path: str
    metadata: Dict = field(default_factory=dict)
    priority: int = 0
    last_accessed: float = 0.0

class ContextHandler:
    def __init__(self, session_dir: str):
        self.session_dir = session_dir
        self.context_items: Dict[str, ContextItem] = {}
        self.context_file = Path(session_dir) / "context.json"
        self._load_context()
        
    def _load_context(self) -> None:
        """Load context from the session's context file if it exists."""
        if self.context_file.exists():
            try:
                with open(self.context_file, 'r') as f:
                    data = json.load(f)
                    for item_data in data:
                        self.context_items[item_data['path']] = ContextItem(**item_data)
            except Exception as e:
                print(f"Error loading context: {e}")

    def _save_context(self) -> None:
        """Save current context to the session's context file."""
        try:
            with open(self.context_file, 'w') as f:
                context_data = [
                    {
                        'type': item.type,
                        'path': item.path,
                        'metadata': item.metadata,
                        'priority': item.priority,
                        'last_accessed': item.last_accessed
                    }
                    for item in self.context_items.values()
                ]
                json.dump(context_data, f, indent=2)
        except Exception as e:
            print(f"Error saving context: {e}")

    def detect_git_repo(self, start_path: str = '.') -> Optional[str]:
        """Detect if the current directory is in a git repository."""
        try:
            repo = git.Repo(start_path, search_parent_directories=True)
            return repo.working_dir
        except git.InvalidGitRepositoryError:
            return None

    def add_git_context(self, repo_path: Optional[str] = None) -> None:
        """Add git repository context if available."""
        if not repo_path:
            repo_path = self.detect_git_repo()
        
        if repo_path:
            try:
                repo = git.Repo(repo_path)
                self.context_items[repo_path] = ContextItem(
                    type="git_repo",
                    path=repo_path,
                    metadata={
                        "current_branch": repo.active_branch.name,
                        "remotes": [remote.url for remote in repo.remotes],
                        "last_commit": str(repo.head.commit.hexsha)
                    },
                    priority=10
                )
                self._save_context()
            except Exception as e:
                print(f"Error adding git context: {e}")

    def add_documentation(self, url: str, title: str, relevance: int = 5) -> None:
        """Add documentation URL to context."""
        self.context_items[url] = ContextItem(
            type="documentation",
            path=url,
            metadata={"title": title},
            priority=relevance
        )
        self._save_context()

    def add_file(self, file_path: str, file_type: str = "source", metadata: Dict = None) -> None:
        """Add a file to the context."""
        abs_path = str(Path(file_path).resolve())
        self.context_items[abs_path] = ContextItem(
            type=file_type,
            path=abs_path,
            metadata=metadata or {}
        )
        self._save_context()

    def add_directory(self, dir_path: str, include_patterns: List[str] = None) -> None:
        """Add a directory and its relevant contents to context."""
        abs_path = str(Path(dir_path).resolve())
        if include_patterns is None:
            include_patterns = ['*.py', '*.js', '*.ts', '*.json', '*.md']
            
        self.context_items[abs_path] = ContextItem(
            type="directory",
            path=abs_path,
            metadata={"include_patterns": include_patterns}
        )
        
        # Add individual files that match patterns
        for pattern in include_patterns:
            for file_path in Path(abs_path).rglob(pattern):
                self.add_file(str(file_path))
        
        self._save_context()

    def get_relevant_context(self, query: str = None, limit: int = 10) -> List[ContextItem]:
        """Get most relevant context items, optionally filtered by query."""
        items = list(self.context_items.values())
        
        # Sort by priority and last accessed time
        items.sort(key=lambda x: (-x.priority, -x.last_accessed))
        
        if query:
            # Simple keyword matching - could be enhanced with more sophisticated matching
            items = [item for item in items if query.lower() in item.path.lower() or 
                    any(query.lower() in str(v).lower() for v in item.metadata.values())]
        
        return items[:limit]

    def clear_context(self) -> None:
        """Clear all context items."""
        self.context_items.clear()
        self._save_context() 