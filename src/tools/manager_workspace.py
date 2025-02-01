import os
from pathlib import Path
import shutil
from typing import List

class WorkspaceManager:
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).resolve()
        
    def _get_full_path(self, relative_path: str) -> Path:
        """Convert a workspace-relative path to full path"""
        full_path = (self.workspace_root / relative_path).resolve()
        if not str(full_path).startswith(str(self.workspace_root)):
            raise Exception("Access denied: Path outside workspace")
        return full_path
    
    def list_directory(self, relative_path: str = "") -> list:
        """List contents of a directory relative to workspace root"""
        full_path = self._get_full_path(relative_path)
        return os.listdir(full_path)
    
    def read_file(self, relative_path: str) -> str:
        """Read file contents using workspace-relative path"""
        full_path = self._get_full_path(relative_path)
        with open(full_path, 'r') as f:
            return f.read()
    
    def write_file(self, relative_path: str, content: str) -> None:
        """Write content to a file using workspace-relative path"""
        full_path = self._get_full_path(relative_path)
        os.makedirs(full_path.parent, exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)
        return f"{relative_path} created successfully."
    
    def delete_file(self, relative_path: str) -> None:
        """Delete a file or directory using workspace-relative path"""
        full_path = self._get_full_path(relative_path)

        # require user input for deletion
        user_input = input(f"Are you sure you want to delete {full_path}? (y/n): ")
        if user_input.lower() != 'y':
            return "Operation cancelled by user."
        
        if full_path.is_dir():
            shutil.rmtree(full_path)
        else:
            full_path.unlink()
        
        return f"{relative_path} deleted successfully."
    
    def search_files(self, pattern: str = "*", content_match: str = None) -> List[str]:
        """Search for files by path pattern and optionally by content"""
        results = []
        for file in self.workspace_root.rglob(pattern):
            if content_match:
                try:
                    with open(file, 'r') as f:
                        if content_match in f.read():
                            results.append(str(file.relative_to(self.workspace_root)))
                except Exception as e:
                    pass
            else:
                results.append(str(file.relative_to(self.workspace_root)))
        return results
