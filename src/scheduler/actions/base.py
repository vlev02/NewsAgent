"""
Base abstract class for scheduler actions.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from src.database import DatabaseManager
from src.dataclasses.config import AgentConfig


class Action(ABC):
    """Abstract base class for all scheduler actions."""

    def __init__(self, db: DatabaseManager, agents_config: Dict[str, AgentConfig]):
        """
        Initialize action.

        Args:
            db: Database manager instance
            agents_config: Dictionary of agent configurations keyed by agent name
        """
        self.db = db
        self.agents_config = agents_config

    @property
    @abstractmethod
    def name(self) -> str:
        """Action name (e.g., 'Explore Recent Research')"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Action description"""
        pass

    @abstractmethod
    def execute(self) -> bool:
        """
        Execute the action.

        Returns:
            bool: True if successful, False if user cancelled or error occurred
        """
        pass
