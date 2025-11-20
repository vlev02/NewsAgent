"""
Path Manager Utility - Centralized path management.

Provides absolute path utilities for accessing project resources.
Auto-detects project root and provides path helpers for:
- Data directories
- Cache directories
- Template directories
- Database paths
- Log paths
"""

from pathlib import Path
from typing import Optional


class PathManager:
    """Centralized path management - all paths are absolute from ROOT_DIR."""

    _ROOT_DIR: Optional[Path] = None

    @classmethod
    def initialize_root(cls, root_dir: Optional[Path] = None) -> Path:
        """
        Initialize ROOT_DIR - the project root directory.

        Args:
            root_dir: Custom root directory. If None, auto-detects project root
                     by finding the parent directory of src/ folder.

        Returns:
            Path: The ROOT_DIR

        Notes:
            Should be called once during application startup.

            Auto-detection works by locating the src/ folder and using its parent,
            which is reliable regardless of where the script is launched from.
        """
        if root_dir:
            cls._ROOT_DIR = root_dir.resolve()
        else:
            # Auto-detect project root by finding src/ folder
            # __file__ = .../NewsAgent/src/utils/path_manager.py
            # So: parent = .../src/utils
            #     parent.parent = .../src
            #     parent.parent.parent = .../NewsAgent (project root)
            current_file = Path(__file__).resolve()
            utils_dir = current_file.parent      # .../src/utils
            src_dir = utils_dir.parent           # .../src
            project_root = src_dir.parent        # .../NewsAgent (or project root)

            # Verify this is actually the project root by checking src/ exists
            if (project_root / "src").exists() and (project_root / "src").is_dir():
                cls._ROOT_DIR = project_root
            else:
                # Fallback to cwd if structure not as expected
                cls._ROOT_DIR = Path.cwd().resolve()

        return cls._ROOT_DIR

    @classmethod
    def get_root(cls) -> Path:
        """Get ROOT_DIR - initializes if not set."""
        if cls._ROOT_DIR is None:
            cls.initialize_root()
        return cls._ROOT_DIR

    @classmethod
    def get_absolute_path(cls, relative_path: str) -> Path:
        """
        Get absolute path by concatenating ROOT_DIR + relative_path.

        Args:
            relative_path: Relative path from ROOT_DIR (e.g., "data/newsagent.db")

        Returns:
            Path: Absolute path resolved

        Examples:
            PathManager.get_absolute_path("data/newsagent.db")
            # → /home/user/NewsAgent/data/newsagent.db

            PathManager.get_absolute_path("data/fake_response/bocha")
            # → /home/user/NewsAgent/data/fake_response/bocha
        """
        return (cls.get_root() / relative_path).resolve()

    @classmethod
    def get_data_dir(cls) -> Path:
        """Get data directory: ROOT_DIR/data"""
        return cls.get_absolute_path("data")

    @classmethod
    def get_cache_dir(cls) -> Path:
        """Get cache directory: ROOT_DIR/data/fake_response"""
        return cls.get_absolute_path("data/fake_response")

    @classmethod
    def get_bocha_cache_dir(cls) -> Path:
        """Get BOCHA cache directory: ROOT_DIR/data/fake_response/bocha"""
        return cls.get_absolute_path("data/fake_response/bocha")

    @classmethod
    def get_agent_cache_dir(cls, agent_name: str) -> Path:
        """
        Get cache directory for a specific agent.

        Args:
            agent_name: Agent name (e.g., "BOCHA", "XUNFEI")

        Returns:
            Path: Cache directory for the agent
        """
        return cls.get_absolute_path(f"data/fake_response/{agent_name.lower()}")

    @classmethod
    def get_templates_dir(cls) -> Path:
        """Get templates directory: ROOT_DIR/src/templates"""
        return cls.get_absolute_path("src/templates")

    @classmethod
    def get_database_path(cls, db_name: str = "newsagent.db") -> Path:
        """Get database path: ROOT_DIR/data/{db_name}"""
        return cls.get_absolute_path(f"data/{db_name}")

    @classmethod
    def get_log_path(cls, log_name: str = "newsagent.log") -> Path:
        """Get log path: ROOT_DIR/{log_name}"""
        return cls.get_absolute_path(log_name)

    @classmethod
    def ensure_dir_exists(cls, path: Path) -> Path:
        """Ensure directory exists, create if needed."""
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def print_paths(cls) -> None:
        """Print all important paths for debugging."""
        print(f"ROOT_DIR:             {cls.get_root()}")
        print(f"Data Directory:       {cls.get_data_dir()}")
        print(f"Cache Directory:      {cls.get_cache_dir()}")
        print(f"BOCHA Cache:          {cls.get_bocha_cache_dir()}")
        print(f"Templates Directory:  {cls.get_templates_dir()}")
        print(f"Database:             {cls.get_database_path()}")
        print(f"Log File:             {cls.get_log_path()}")
