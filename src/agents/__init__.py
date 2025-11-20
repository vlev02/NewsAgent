"""Search agents for various data sources"""

from .base import SearchAgent
from .request_schema import RequestSchema
from .manager import AgentManager, get_agent_manager
from .agent_bocha import BochaAgent, BochaRequestSchema

# AgentConfig is imported from src.dataclasses to avoid duplication
from src.dataclasses import AgentConfig


__all__ = [
    "SearchAgent",
    "RequestSchema",
    "AgentManager",
    "AgentConfig",
    "get_agent_manager",
]
