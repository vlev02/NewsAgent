"""
Scheduler Settings Manager - Comprehensive environment and configuration initialization.

This module handles:
1. Loading .env file with environment variables
2. Initializing scheduler configuration
3. Initializing all agent configurations with API keys
4. Validating configurations
5. Providing runtime settings access
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
    def initialize(cls, env_file: str = ".env") -> "SchedulerSettings":
        """
        Initialize scheduler settings from .env file and environment.

        Args:
            env_file: Path to .env file (default: .env in project root)

        Returns:
            SchedulerSettings instance with all configurations initialized
        """
        # Find project root
        project_root = Path.cwd()
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
