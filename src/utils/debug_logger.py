"""
Debug Logger

Provides logging for debug operations with color-coded output.
Only logs when DebugConfig.DEBUG is True.
"""

import logging
from typing import Optional

from src.debug_config import DebugConfig


class DebugLogger:
    """Logger for debug operations with color-coded output."""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[92m',       # Green
        'WARNING': '\033[93m',    # Yellow
        'ERROR': '\033[91m',      # Red
        'RESET': '\033[0m',       # Reset
        'BOLD': '\033[1m',        # Bold
    }

    def __init__(self, name: str):
        """
        Initialize debug logger.

        Args:
            name: Logger name (typically __name__)
        """
        self.name = name
        self.logger = logging.getLogger(f"[DEBUG] {name}")

    def debug(self, message: str):
        """Log debug message."""
        if DebugConfig.DEBUG and DebugConfig.log_level in ('DEBUG',):
            self._log('DEBUG', message)

    def info(self, message: str):
        """Log info message."""
        if DebugConfig.DEBUG and DebugConfig.log_level in ('DEBUG', 'INFO'):
            self._log('INFO', message)

    def warning(self, message: str):
        """Log warning message."""
        if DebugConfig.DEBUG:
            self._log('WARNING', message)

    def error(self, message: str):
        """Log error message."""
        if DebugConfig.DEBUG:
            self._log('ERROR', message)

    def _log(self, level: str, message: str):
        """
        Internal logging method with color output.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR)
            message: Log message
        """
        color = self.COLORS.get(level, '')
        reset = self.COLORS['RESET']
        timestamp = self._get_timestamp()

        # Format: [TIMESTAMP] [LEVEL] [MODULE] message
        formatted = (
            f"{color}[{timestamp}] [{level}] [{self.name}] {message}{reset}"
        )
        print(formatted)

        # Also log to standard logger
        logger = logging.getLogger(self.name)
        getattr(logger, level.lower())(message)

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp in HH:MM:SS format."""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")

    @staticmethod
    def print_section(title: str):
        """Print a formatted section header."""
        if DebugConfig.DEBUG:
            color = DebugLogger.COLORS['BOLD'] + DebugLogger.COLORS['DEBUG']
            reset = DebugLogger.COLORS['RESET']
            print(f"\n{color}→ {title}{reset}")

    @staticmethod
    def print_table(headers: list, rows: list):
        """Print a formatted table."""
        if not DebugConfig.DEBUG:
            return

        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))

        # Print header
        header_line = " | ".join(f"{h:{w}}" for h, w in zip(headers, col_widths))
        print(f"\n{DebugLogger.COLORS['BOLD']}{header_line}{DebugLogger.COLORS['RESET']}")
        print("-" * len(header_line))

        # Print rows
        for row in rows:
            row_line = " | ".join(f"{str(v):{w}}" for v, w in zip(row, col_widths))
            print(row_line)


def print_debug_header(message: str):
    """Print debug header message."""
    if DebugConfig.DEBUG:
        color = DebugLogger.COLORS['BOLD'] + DebugLogger.COLORS['DEBUG']
        reset = DebugLogger.COLORS['RESET']
        width = 70
        print(f"\n{color}{'=' * width}")
        print(f"{message.center(width)}")
        print(f"{'=' * width}{reset}\n")


def print_debug_info(message: str):
    """Print debug info message."""
    if DebugConfig.DEBUG:
        color = DebugLogger.COLORS['INFO']
        reset = DebugLogger.COLORS['RESET']
        print(f"{color}ℹ️  {message}{reset}")


def print_debug_warning(message: str):
    """Print debug warning message."""
    if DebugConfig.DEBUG:
        color = DebugLogger.COLORS['WARNING']
        reset = DebugLogger.COLORS['RESET']
        print(f"{color}⚠️  {message}{reset}")


def print_debug_error(message: str):
    """Print debug error message."""
    if DebugConfig.DEBUG:
        color = DebugLogger.COLORS['ERROR']
        reset = DebugLogger.COLORS['RESET']
        print(f"{color}❌ {message}{reset}")


def print_debug_success(message: str):
    """Print debug success message."""
    if DebugConfig.DEBUG:
        color = DebugLogger.COLORS['INFO']
        reset = DebugLogger.COLORS['RESET']
        print(f"{color}✅ {message}{reset}")
