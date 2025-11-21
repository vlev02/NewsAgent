"""
Environment variable loader for NewsAgent.

Loads configuration from .env file when the module is imported.
Requires python-dotenv package.
"""

import os
import warnings
from pathlib import Path
from typing import Optional

# Direct import - dotenv is required
from dotenv import load_dotenv


class EnvLoader:
    """Utility class for loading and managing environment variables from .env file."""

    _loaded: bool = False
    _env_path: Optional[Path] = None

    @classmethod
    def load(cls, env_path: Optional[str] = None) -> None:
        """
        Load environment variables from .env file.

        Args:
            env_path: Path to .env file. If None, searches in common locations.

        Warnings:
            UserWarning: If .env file cannot be found in expected locations.

        Raises:
            ImportError: If python-dotenv is not installed.
        """
        if cls._loaded:
            return

        # Determine .env file path
        if env_path:
            env_file = Path(env_path)
        else:
            # Search for .env in common locations
            env_file = cls._find_env_file()

        if env_file and env_file.exists():
            # Load environment variables from .env file
            load_dotenv(env_file)
            cls._env_path = env_file
            cls._loaded = True
            print(f"✓ Environment loaded from: {env_file}")
        else:
            # Warn if .env file not found
            warning_msg = (
                "⚠ .env file not found. Environment variables will not be loaded from .env. "
                "API keys must be set via environment variables or programmatically. "
                "Searched in: current directory, project root, and parent directories."
            )
            warnings.warn(warning_msg, UserWarning, stacklevel=3)
            cls._loaded = True

    @classmethod
    def _find_env_file(cls) -> Optional[Path]:
        """
        Find .env file in common locations.

        Search order:
        1. Current working directory
        2. Project root (parent of src directory)
        3. Parent directories up to 3 levels

        Returns:
            Path to .env file if found, None otherwise
        """
        search_paths = [
            Path.cwd() / ".env",  # Current working directory
            Path(__file__).parent.parent.parent / ".env",  # Project root
        ]

        # Add parent directories (up to 3 levels from current file)
        current = Path(__file__).parent
        for _ in range(3):
            current = current.parent
            search_paths.append(current / ".env")

        for path in search_paths:
            if path.exists() and path.is_file():
                return path

        return None

    @classmethod
    def get_env_path(cls) -> Optional[Path]:
        """
        Get the path of the loaded .env file.

        Returns:
            Path to .env file if loaded, None otherwise
        """
        return cls._env_path

    @classmethod
    def is_loaded(cls) -> bool:
        """
        Check if environment has been loaded.

        Returns:
            True if load() was called, False otherwise
        """
        return cls._loaded

    @classmethod
    def get(cls, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get environment variable with automatic loading.

        Args:
            key: Environment variable name
            default: Default value if not found

        Returns:
            Environment variable value or default
        """
        if not cls._loaded:
            cls.load()

        return os.environ.get(key, default)


# Auto-load environment on module import
EnvLoader.load()
