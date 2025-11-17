"""
Scheduler configuration loader.
"""

import os
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass
from src.dataclasses.config import (
    XUNFEI_CONFIG, BOCHA_CONFIG, HUNYUAN_CONFIG,
    QIANFAN_CONFIG, META_CONFIG, TWITTER_CONFIG
)


@dataclass
class SchedulerConfig:
    """Configuration for the scheduler."""

    database_path: str = "newsagent.db"
    log_level: str = "INFO"
    log_file: str = "newsagent.log"
    default_time_range_days: int = 7
    default_max_results: int = 10
    export_directory: str = "data"

    @classmethod
    def from_env(cls) -> "SchedulerConfig":
        """Load configuration from environment variables."""
        return cls(
            database_path=os.getenv("DATABASE_PATH", "newsagent.db"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE", "newsagent.log"),
            default_time_range_days=int(os.getenv("DEFAULT_TIME_RANGE", "7")),
            default_max_results=int(os.getenv("DEFAULT_MAX_RESULTS", "10")),
            export_directory=os.getenv("EXPORT_DIRECTORY", "data"),
        )

    @classmethod
    def from_file(cls, config_file: str) -> "SchedulerConfig":
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls(**data)
        except Exception as e:
            print(f"Warning: Failed to load config file {config_file}: {e}")
            return cls.from_env()


def get_agent_configs() -> Dict[str, Any]:
    """Get all pre-configured agent configs."""
    configs = {
        "XUNFEI": XUNFEI_CONFIG,
        "BOCHA": BOCHA_CONFIG,
        "HUNYUAN": HUNYUAN_CONFIG,
        "QIANFAN": QIANFAN_CONFIG,
        "META": META_CONFIG,
        "TWITTER": TWITTER_CONFIG,
    }

    # Load API keys from environment
    for name, config in configs.items():
        api_key_env = f"{name}_API_KEY"
        if name == "XUNFEI":
            # XUNFEI has special configuration
            config.api_key = os.getenv("XUNFEI_APPID")
        elif name == "TWITTER":
            config.api_key = os.getenv("TWITTER_BEARER_TOKEN")
        else:
            config.api_key = os.getenv(api_key_env)

    return configs
