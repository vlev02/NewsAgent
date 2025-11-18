"""
Debug Configuration Module

Global configuration for debugging and fake response system.
Controls behavior of fake response caching, logging, and user interaction.

This module is NOT committed to git - for development use only.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class DebugConfig:
    """
    Global debug configuration for the NewsAgent scheduler and agents.

    All attributes can be modified at runtime to control fake response behavior.

    Attributes:
        DEBUG: Enable/disable all debug features
        fake_response_enabled: Use cached fake responses instead of real API calls
        fake_response_update: Replace cached response file for specific request
        fake_response_interact: Ask user interactively for each operation
        fake_response_dir: Directory to store fake responses
        log_fake_response_hits: Log when cached response is found
        log_fake_response_misses: Log when cached response is not found
        log_api_calls: Log all API calls with details
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """

    # Main debug flag
    DEBUG: bool = False

    # Fake response control flags
    fake_response_enabled: bool = True
    fake_response_update: bool = True
    fake_response_interact: bool = False

    # Directory for fake responses
    fake_response_dir: str = "data/fake_response"

    # Logging flags
    log_fake_response_hits: bool = True
    log_fake_response_misses: bool = True
    log_api_calls: bool = True
    log_decorator_calls: bool = True

    # Logging level
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR

    # Session flag to skip interaction for remaining operations
    _skip_interaction_for_session: bool = False

    @classmethod
    def enable_debug(cls):
        """Enable all debug features."""
        cls.DEBUG = True
        cls.fake_response_enabled = True
        cls.log_fake_response_hits = True
        cls.log_fake_response_misses = True
        cls.log_api_calls = True
        cls.log_decorator_calls = True

    @classmethod
    def disable_debug(cls):
        """Disable all debug features."""
        cls.DEBUG = False
        cls.fake_response_enabled = False
        cls.log_fake_response_hits = False
        cls.log_fake_response_misses = False
        cls.log_api_calls = False
        cls.log_decorator_calls = False

    @classmethod
    def enable_fake_responses(cls):
        """Enable fake response caching."""
        cls.fake_response_enabled = True

    @classmethod
    def disable_fake_responses(cls):
        """Disable fake response caching."""
        cls.fake_response_enabled = False

    @classmethod
    def enable_interactive(cls):
        """Enable interactive mode (requires DEBUG=True)."""
        cls.fake_response_interact = True

    @classmethod
    def disable_interactive(cls):
        """Disable interactive mode."""
        cls.fake_response_interact = False

    @classmethod
    def set_update_mode(cls, enabled: bool):
        """Set whether to update cached responses when calling real API."""
        cls.fake_response_update = enabled

    @classmethod
    def set_fake_response_dir(cls, directory: str):
        """Set the directory for storing fake responses."""
        cls.fake_response_dir = directory
        Path(directory).mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_config_summary(cls) -> str:
        """Return a summary of current debug configuration."""
        return f"""
Debug Configuration Summary:
  DEBUG:                           {cls.DEBUG}
  fake_response_enabled:           {cls.fake_response_enabled}
  fake_response_update:            {cls.fake_response_update}
  fake_response_interact:          {cls.fake_response_interact}
  fake_response_dir:               {cls.fake_response_dir}
  log_fake_response_hits:          {cls.log_fake_response_hits}
  log_fake_response_misses:        {cls.log_fake_response_misses}
  log_api_calls:                   {cls.log_api_calls}
  log_decorator_calls:             {cls.log_decorator_calls}
  log_level:                       {cls.log_level}
"""


# Global config instance for convenience
debug_config = DebugConfig()


def enable_debug():
    """Convenience function to enable debug mode."""
    DebugConfig.enable_debug()


def disable_debug():
    """Convenience function to disable debug mode."""
    DebugConfig.disable_debug()


def print_debug_config():
    """Print current debug configuration."""
    print(DebugConfig.get_config_summary())
