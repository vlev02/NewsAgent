"""Search agents for various data sources"""

# Load environment variables first (before agent manager initialization)
from src.utils import EnvLoader

from .base import SearchAgent
from .request_schema import RequestSchema
from .manager import AgentManager, get_agent_manager
from .agent_bocha import BochaAgent, BochaRequestSchema
from .config import AgentConfig


__all__ = [
    "SearchAgent",
    "RequestSchema",
    "AgentManager",
    "AgentConfig",
    "get_agent_manager",
]
