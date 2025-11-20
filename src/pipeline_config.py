"""
Pipeline Configuration Manager - Agent instantiation and pipeline setup.

This module handles:
1. Creating SearchAgent instances from AgentConfig objects
2. Initializing the SearchPipeline with agents
3. Providing factory methods for agent creation

IMPORTANT: This module receives AgentConfig objects from src/dataclasses/config.py ONLY.
All agent instantiation logic is centralized here.
"""

from typing import Dict
from src.dataclasses.config import AgentConfig
from src.agents.base import SearchAgent
from src.agents.agent_bocha import BochaAgent
from src.pipeline import SearchPipeline
from src.database.manager import DatabaseManager


# Agent factory mapping
_AGENT_FACTORY_MAP = {
    "BOCHA": BochaAgent,
    # More agents can be added here (XUNFEI, HUNYUAN, META, TWITTER, QIANFAN)
}


def create_agent(agent_name: str, config: AgentConfig) -> SearchAgent:
    """
    Create a SearchAgent instance from AgentConfig.

    Args:
        agent_name: Name of the agent (e.g., "BOCHA", "XUNFEI")
        config: AgentConfig object from src/dataclasses/config.py

    Returns:
        SearchAgent instance ready for use

    Raises:
        ValueError: If agent type is not supported
    """
    if agent_name not in _AGENT_FACTORY_MAP:
        raise ValueError(
            f"Unsupported agent: {agent_name}. "
            f"Supported agents: {', '.join(_AGENT_FACTORY_MAP.keys())}"
        )

    agent_class = _AGENT_FACTORY_MAP[agent_name]
    return agent_class(config)


def create_agents_from_configs(agent_configs: Dict[str, AgentConfig]) -> Dict[str, SearchAgent]:
    """
    Create SearchAgent instances from a dictionary of AgentConfigs.

    Args:
        agent_configs: Dict mapping agent names to AgentConfig objects
                      (from SchedulerSettings.agent_configs)

    Returns:
        Dict mapping agent names to SearchAgent instances
    """
    agents = {}
    for agent_name, config in agent_configs.items():
        try:
            agent = create_agent(agent_name, config)
            agents[agent_name] = agent
        except ValueError as e:
            print(f"Warning: Could not create agent {agent_name}: {e}")
            continue
    return agents


def initialize_pipeline(agent_configs: Dict[str, AgentConfig],
                       db_manager: DatabaseManager) -> SearchPipeline:
    """
    Initialize a SearchPipeline with agents from AgentConfigs.

    Args:
        agent_configs: Dict mapping agent names to AgentConfig objects
        db_manager: DatabaseManager instance for persistence

    Returns:
        SearchPipeline ready for query execution
    """
    # Create agent instances
    agents = create_agents_from_configs(agent_configs)

    if not agents:
        raise ValueError("No agents could be initialized. Check agent configurations.")

    # Create and return pipeline
    return SearchPipeline(agents, db_manager)
