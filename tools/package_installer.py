import importlib.util
import subprocess
import sys
import os
from typing import Tuple, Optional

class PackageInstaller:
    def __init__(self):
        self.is_venv = self._check_venv()
        self.package_manager = self._detect_package_manager()
    
    def _check_venv(self) -> bool:
        """Check if running in a Python virtual environment"""
        return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    def _detect_package_manager(self) -> str:
        """Detect the appropriate package manager"""
        if os.path.exists('poetry.lock'):
            return 'poetry'
        elif os.path.exists('Pipfile'):
            return 'pipenv'
        else:
            return 'pip'
    
    def is_package_installed(self, package_name: str) -> bool:
        """Check if a Python package is installed"""
        try:
            spec = importlib.util.find_spec(package_name)
            return spec is not None
        except ModuleNotFoundError:
            return False
    
    def install_package(self, package_name: str) -> Tuple[bool, Optional[str]]:
        """
        Install a package using the detected package manager
        Returns: (success: bool, error_message: Optional[str])
        """
        if self.is_package_installed(package_name):
            return True, None
            
        try:
            if not self.is_venv and self.package_manager == 'pip':
                return False, "Attempting to install packages outside of virtual environment. Please activate your venv first."
            
            commands = {
                'pip': f"{sys.executable} -m pip install {package_name}",
                'poetry': f"poetry add {package_name}",
                'pipenv': f"pipenv install {package_name}"
            }
            
            command = commands[self.package_manager]
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return True, None
            else:
                return False, f"Installation failed: {result.stderr}"
                
        except Exception as e:
            return False, f"Installation error: {str(e)}" 