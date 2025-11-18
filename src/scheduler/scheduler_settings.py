"""
Scheduler Settings Manager - Comprehensive environment and configuration initialization.

This module handles:
1. Loading .env file with environment variables
2. Initializing scheduler configuration
3. Initializing all agent configurations with API keys
4. Validating configurations
5. Providing runtime settings access
6. Managing all absolute paths from ROOT_DIR
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from dotenv import load_dotenv

from src.scheduler.interactive import (
    print_section, print_item, print_success, print_warning, print_error, print_info
)
from src.dataclasses.config import (
    XUNFEI_CONFIG, BOCHA_CONFIG, HUNYUAN_CONFIG,
    QIANFAN_CONFIG, META_CONFIG, TWITTER_CONFIG, AgentConfig
)


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
            # __file__ = .../NewsAgent/src/scheduler/scheduler_settings.py
            # So: parent = .../src/scheduler
            #     parent.parent = .../src
            #     parent.parent.parent = .../NewsAgent (project root)
            current_file = Path(__file__).resolve()
            scheduler_dir = current_file.parent  # .../src/scheduler
            src_dir = scheduler_dir.parent       # .../src
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


@dataclass
class EnvironmentVariables:
    """Container for all environment variables."""

    # XUNFEI Configuration
    xunfei_appid: Optional[str] = None
    xunfei_api_secret: Optional[str] = None
    xunfei_api_key: Optional[str] = None
    xunfei_api_password: Optional[str] = None

    # Tencent Hunyuan Configuration
    hunyuan_secret_id: Optional[str] = None
    hunyuan_secret_key: Optional[str] = None
    hunyuan_api_key: Optional[str] = None

    # BOCHA Configuration
    bocha_api_key: Optional[str] = None

    # Baidu Qianfan Configuration
    qianfan_api_key: Optional[str] = None

    # MetaSo Configuration
    meta_api_key: Optional[str] = None

    # Twitter/X Configuration
    twitter_bearer_token: Optional[str] = None

    # Database Configuration
    database_path: str = "data/newsagent.db"
    log_level: str = "INFO"
    log_file: str = "newsagent.log"
    export_directory: str = "data"

    # Scheduler Configuration
    default_time_range_days: int = 7
    default_max_results: int = 10

    # Optional Proxy Configuration
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None

    @classmethod
    def from_env(cls) -> "EnvironmentVariables":
        """Load all environment variables."""
        return cls(
            # XUNFEI
            xunfei_appid=os.getenv("XUNFEI_APPID"),
            xunfei_api_secret=os.getenv("XUNFEI_APISecret"),
            xunfei_api_key=os.getenv("XUNFEI_APIKey"),
            xunfei_api_password=os.getenv("XUNFEI_APIPassword"),

            # Hunyuan
            hunyuan_secret_id=os.getenv("HUNYUAN_SECRET_ID"),
            hunyuan_secret_key=os.getenv("HUNYUAN_SECRET_KEY"),
            hunyuan_api_key=os.getenv("HUNYUAN_API_KEY"),

            # BOCHA
            bocha_api_key=os.getenv("BOCHA_API_KEY"),

            # Qianfan
            qianfan_api_key=os.getenv("QIANFAN_API_KEY"),

            # MetaSo
            meta_api_key=os.getenv("META_API_KEY"),

            # Twitter
            twitter_bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),

            # Database & Logging
            database_path=os.getenv("DATABASE_PATH", "data/newsagent.db"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE", "newsagent.log"),
            export_directory=os.getenv("EXPORT_DIRECTORY", "data"),

            # Scheduler
            default_time_range_days=int(os.getenv("DEFAULT_TIME_RANGE", "7")),
            default_max_results=int(os.getenv("DEFAULT_MAX_RESULTS", "10")),

            # Proxy
            http_proxy=os.getenv("HTTP_PROXY"),
            https_proxy=os.getenv("HTTPS_PROXY"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for display."""
        return {
            "xunfei_appid": "***" if self.xunfei_appid else "NOT SET",
            "xunfei_api_key": "***" if self.xunfei_api_key else "NOT SET",
            "hunyuan_api_key": "***" if self.hunyuan_api_key else "NOT SET",
            "bocha_api_key": "***" if self.bocha_api_key else "NOT SET",
            "qianfan_api_key": "***" if self.qianfan_api_key else "NOT SET",
            "meta_api_key": "***" if self.meta_api_key else "NOT SET",
            "twitter_bearer_token": "***" if self.twitter_bearer_token else "NOT SET",
            "database_path": self.database_path,
            "log_level": self.log_level,
            "log_file": self.log_file,
            "export_directory": self.export_directory,
        }


@dataclass
class SchedulerSettings:
    """Complete scheduler settings including all configurations."""

    env_vars: EnvironmentVariables
    scheduler_config: Dict[str, Any] = field(default_factory=dict)
    agent_configs: Dict[str, AgentConfig] = field(default_factory=dict)
    agents_status: Dict[str, Tuple[bool, str]] = field(default_factory=dict)

    @classmethod
    def initialize(cls, env_file: str = ".env", root_dir: Optional[Path] = None, **overrides) -> "SchedulerSettings":
        """
        Initialize scheduler settings from .env file with optional overrides.

        This is the SINGLE entry point for all environment configuration in NewsAgent.

        Args:
            env_file: Path to .env file (default: .env in project root)
            root_dir: Project root directory (default: current working directory)
            **overrides: Environment variable overrides as keyword arguments.
                        Any field from EnvironmentVariables dataclass can be overridden.

        Returns:
            SchedulerSettings instance with all configurations initialized

        Examples:
            # Use default .env
            settings = SchedulerSettings.initialize()

            # Use custom .env file
            settings = SchedulerSettings.initialize(".env.production")

            # Override specific values (inherits rest from .env)
            settings = SchedulerSettings.initialize(
                database_path="data/test.db",
                log_level="DEBUG",
                bocha_api_key="test-key"
            )

            # Combine custom file + overrides
            settings = SchedulerSettings.initialize(
                ".env.staging",
                database_path="data/staging.db"
            )

        Supported override keys:
            # API Keys
            - xunfei_appid, xunfei_api_secret, xunfei_api_key, xunfei_api_password
            - hunyuan_secret_id, hunyuan_secret_key, hunyuan_api_key
            - bocha_api_key
            - qianfan_api_key
            - meta_api_key
            - twitter_bearer_token

            # Configuration
            - database_path (str)
            - log_level (str)
            - log_file (str)
            - export_directory (str)
            - default_time_range_days (int)
            - default_max_results (int)
            - http_proxy (str)
            - https_proxy (str)

        Override Priority:
            1. **overrides (highest priority)
            2. Environment variables from .env file
            3. Default values in EnvironmentVariables dataclass
        """
        # Initialize PathManager with ROOT_DIR
        PathManager.initialize_root(root_dir)
        project_root = PathManager.get_root()

        # Find .env file
        env_path = project_root / env_file

        # Load .env file
        if env_path.exists():
            load_dotenv(env_path)
        else:
            # Try parent directory
            parent_env = project_root.parent / env_file
            if parent_env.exists():
                load_dotenv(parent_env)

        # Load environment variables
        env_vars = EnvironmentVariables.from_env()

        # Convert relative paths to absolute paths
        if 'database_path' not in overrides:
            env_vars.database_path = str(PathManager.get_database_path())

        if 'log_file' not in overrides:
            env_vars.log_file = str(PathManager.get_log_path())

        if 'export_directory' not in overrides:
            env_vars.export_directory = str(PathManager.get_data_dir())

        # Apply overrides to env_vars
        for key, value in overrides.items():
            if hasattr(env_vars, key):
                setattr(env_vars, key, value)
            else:
                print_warning(f"Unknown override key: {key} (ignored)")

        # Create scheduler settings
        settings = cls(env_vars=env_vars)

        # Initialize configurations
        settings._initialize_scheduler_config()
        settings._initialize_agent_configs()
        settings._check_agent_status()

        return settings

    def _initialize_scheduler_config(self) -> None:
        """Initialize scheduler configuration from environment variables."""
        self.scheduler_config = {
            "database_path": self.env_vars.database_path,
            "log_level": self.env_vars.log_level,
            "log_file": self.env_vars.log_file,
            "export_directory": self.env_vars.export_directory,
            "default_time_range_days": self.env_vars.default_time_range_days,
            "default_max_results": self.env_vars.default_max_results,
        }

    def _initialize_agent_configs(self) -> None:
        """Initialize all agent configurations with API keys from environment."""
        # Create copies of agent configs to avoid modifying originals
        configs = {
            "XUNFEI": XUNFEI_CONFIG,
            "BOCHA": BOCHA_CONFIG,
            "HUNYUAN": HUNYUAN_CONFIG,
            "QIANFAN": QIANFAN_CONFIG,
            "META": META_CONFIG,
            "TWITTER": TWITTER_CONFIG,
        }

        for agent_name, config in configs.items():
            # Set API keys from environment
            if agent_name == "XUNFEI":
                config.api_key = self.env_vars.xunfei_appid or None
            elif agent_name == "BOCHA":
                config.api_key = self.env_vars.bocha_api_key or None
            elif agent_name == "HUNYUAN":
                config.api_key = self.env_vars.hunyuan_api_key or None
            elif agent_name == "QIANFAN":
                config.api_key = self.env_vars.qianfan_api_key or None
            elif agent_name == "META":
                config.api_key = self.env_vars.meta_api_key or None
            elif agent_name == "TWITTER":
                config.api_key = self.env_vars.twitter_bearer_token or None

            self.agent_configs[agent_name] = config

    def _check_agent_status(self) -> None:
        """Check which agents have valid API keys configured."""
        for agent_name, config in self.agent_configs.items():
            has_key = config.api_key is not None and config.api_key != "your_*_here"
            status = "✓ Ready" if has_key else "✗ Missing API Key"
            self.agents_status[agent_name] = (has_key, status)

    def get_ready_agents(self) -> Dict[str, AgentConfig]:
        """Get only agents with API keys configured."""
        return {
            name: config
            for name, (ready, _) in self.agents_status.items()
            if ready
            for config in [self.agent_configs[name]]
        }

    def get_unavailable_agents(self) -> Dict[str, str]:
        """Get agents without API keys and their environment variable names."""
        unavailable = {}
        env_mapping = {
            "XUNFEI": "XUNFEI_APPID",
            "BOCHA": "BOCHA_API_KEY",
            "HUNYUAN": "HUNYUAN_API_KEY",
            "QIANFAN": "QIANFAN_API_KEY",
            "META": "META_API_KEY",
            "TWITTER": "TWITTER_BEARER_TOKEN",
        }

        for name, (ready, _) in self.agents_status.items():
            if not ready:
                unavailable[name] = env_mapping.get(name, f"{name}_API_KEY")

        return unavailable

    def print_summary(self) -> None:
        """Print a formatted summary of all settings."""
        print_section("Scheduler Settings Summary")

        # Database & Logging
        print_item("Database Path", self.env_vars.database_path)
        print_item("Log Level", self.env_vars.log_level)
        print_item("Log File", self.env_vars.log_file)
        print_item("Export Directory", self.env_vars.export_directory)
        print()

        # Scheduler Defaults
        print_section("Scheduler Defaults")
        print_item("Default Time Range", f"{self.env_vars.default_time_range_days} days")
        print_item("Default Max Results", str(self.env_vars.default_max_results))
        print()

        # Agent Status
        print_section("Agent Configuration Status")
        ready_count = sum(1 for ready, _ in self.agents_status.values() if ready)
        total_count = len(self.agents_status)
        print_item("Ready Agents", f"{ready_count}/{total_count}")
        print()

        for agent_name, (ready, status) in self.agents_status.items():
            emoji = "✓" if ready else "✗"
            print_item(f"  {agent_name}", f"{emoji} {status}", indent=1)

    def print_env_status(self) -> None:
        """Print detailed environment variable status."""
        print_section("Environment Variables Status")

        env_mapping = {
            "XUNFEI": [
                ("XUNFEI_APPID", self.env_vars.xunfei_appid),
                ("XUNFEI_APISecret", self.env_vars.xunfei_api_secret),
                ("XUNFEI_APIKey", self.env_vars.xunfei_api_key),
            ],
            "BOCHA": [("BOCHA_API_KEY", self.env_vars.bocha_api_key)],
            "HUNYUAN": [
                ("HUNYUAN_API_KEY", self.env_vars.hunyuan_api_key),
                ("HUNYUAN_SECRET_ID", self.env_vars.hunyuan_secret_id),
                ("HUNYUAN_SECRET_KEY", self.env_vars.hunyuan_secret_key),
            ],
            "QIANFAN": [("QIANFAN_API_KEY", self.env_vars.qianfan_api_key)],
            "META": [("META_API_KEY", self.env_vars.meta_api_key)],
            "TWITTER": [("TWITTER_BEARER_TOKEN", self.env_vars.twitter_bearer_token)],
        }

        for agent_name, env_vars in env_mapping.items():
            print_item(agent_name, "", indent=0)
            for var_name, var_value in env_vars:
                status = "✓ SET" if var_value else "✗ NOT SET"
                print_item(f"  {var_name}", status, indent=1)

    def validate_critical_config(self) -> bool:
        """
        Validate that at least one agent is configured.

        Returns:
            bool: True if valid, False otherwise
        """
        ready_agents = self.get_ready_agents()

        if not ready_agents:
            print_error("No agents configured! At least one agent needs an API key.")
            print_info("Please configure API keys in .env file:")
            unavailable = self.get_unavailable_agents()
            for agent, env_var in unavailable.items():
                print_info(f"  - {env_var} for {agent}")
            return False

        print_success(f"✓ At least one agent is configured ({len(ready_agents)} ready)")
        return True

    def setup_proxies(self) -> None:
        """Setup proxy environment variables if configured."""
        if self.env_vars.http_proxy:
            os.environ["HTTP_PROXY"] = self.env_vars.http_proxy
            print_info(f"HTTP Proxy: {self.env_vars.http_proxy}")

        if self.env_vars.https_proxy:
            os.environ["HTTPS_PROXY"] = self.env_vars.https_proxy
            print_info(f"HTTPS Proxy: {self.env_vars.https_proxy}")

    def create_export_directory(self) -> None:
        """Create export directory if it doesn't exist."""
        try:
            Path(self.env_vars.export_directory).mkdir(parents=True, exist_ok=True)
            print_success(f"Export directory ready: {self.env_vars.export_directory}")
        except Exception as e:
            print_warning(f"Failed to create export directory: {e}")

    def validate_database_path(self) -> bool:
        """
        Validate that database directory exists and is writable.

        Returns:
            bool: True if valid, False otherwise
        """
        db_path = Path(self.env_vars.database_path)
        db_dir = db_path.parent

        try:
            db_dir.mkdir(parents=True, exist_ok=True)
            # Try to write a test file
            test_file = db_dir / ".write_test"
            test_file.touch()
            test_file.unlink()
            print_success(f"Database directory is writable: {db_dir}")
            return True
        except Exception as e:
            print_error(f"Database directory not writable: {e}")
            return False

    def full_initialization_report(self) -> bool:
        """
        Run complete initialization and report status.

        Returns:
            bool: True if all critical checks pass, False otherwise
        """
        print_section("NewsAgent Scheduler - Initialization Report")
        print()

        # Print configuration summary
        self.print_summary()
        print()

        # Print environment status
        self.print_env_status()
        print()

        # Validate and setup
        print_section("System Checks")

        # Check database path
        db_valid = self.validate_database_path()
        print()

        # Create export directory
        self.create_export_directory()
        print()

        # Setup proxies if configured
        if self.env_vars.http_proxy or self.env_vars.https_proxy:
            print_section("Proxy Configuration")
            self.setup_proxies()
            print()

        # Validate at least one agent is configured
        config_valid = self.validate_critical_config()
        print()

        return db_valid and config_valid


def initialize_scheduler_settings(env_file: str = ".env") -> Optional[SchedulerSettings]:
    """
    Initialize scheduler settings from .env file.

    This is the main entry point for scheduler initialization.

    Args:
        env_file: Path to .env file

    Returns:
        SchedulerSettings instance or None if initialization fails
    """
    try:
        settings = SchedulerSettings.initialize(env_file)
        return settings
    except Exception as e:
        print_error(f"Failed to initialize scheduler settings: {e}")
        return None
