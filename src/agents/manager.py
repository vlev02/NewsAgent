"""Agent Manager - Centralized agent instantiation and lifecycle management"""

import yaml
from pathlib import Path
from typing import Dict, Any, Type, Optional
from dataclasses import dataclass, field

from src.agents.base import SearchAgent
from src.agents.agent_bocha import BochaAgent


@dataclass
class AgentConfig:
    """
    Configuration for a specific search agent.

    All configuration is loaded from config/agents.yaml.
    No hardcoded defaults should exist in code.
    """
    # Identity
    agent_name: str
    agent_type: str  # "LLM_SEARCH" | "REST_API" | "SOCIAL_MEDIA"

    # Authentication
    api_key: str
    api_endpoint: str
    auth_header_name: str = "Authorization"
    auth_prefix: str = "Bearer"

    # Default parameters for API calls (from agents.yaml defaults)
    default_params: Dict[str, Any] = field(default_factory=dict)


class AgentManager:
    """
    Centralized manager for agent instantiation and lifecycle.

    Responsibilities:
    - Load agent configurations from YAML
    - Maintain registry of all implemented agents
    - Instantiate agents with proper configuration
    - Provide agent marketplace (available agents)
    - Ensure each agent maintains its RequestSchema
    """

    # Registry of implemented agent classes
    _AGENT_REGISTRY: Dict[str, Type[SearchAgent]] = {
        "BOCHA": BochaAgent,
        # Future agents:
        # "XUNFEI": XunfeiAgent,
        # "HUNYUAN": HunyuanAgent,
        # "QIANFAN": QianfanAgent,
        # "META": MetaAgent,
        # "TWITTER": TwitterAgent,
    }

    def __init__(self, config_path: str = "config/agents.yaml"):
        """
        Initialize AgentManager.

        Args:
            config_path: Path to agents.yaml configuration file
        """
        self.config_path = config_path
        self._agent_configs: Dict[str, AgentConfig] = {}
        self._load_configurations()

    def _load_configurations(self) -> None:
        """
        Load agent configurations from YAML file using Hydra-style hierarchy.

        Config resolution order (inheritance):
        1. Base agent config (base_agent: auth_header, auth_prefix, language)
        2. Agent type config (agent_types: LLM_SEARCH, REST_API, SOCIAL_MEDIA)
        3. Agent-specific query_body (only override what's needed)

        YAML Structure:
        - base_agent: Base config for all agents (auth, language)
        - agent_types: Config by agent type (type-specific defaults)
        - agents: Agent-specific configs with query_body (request parameters)

        Raises:
            FileNotFoundError: If configuration file not found
        """
        # Resolve path relative to project root
        project_root = Path(__file__).parent.parent.parent
        config_file = project_root / self.config_path

        if not config_file.exists():
            raise FileNotFoundError(f"Agent config file not found: {config_file}")

        with open(config_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # Extract configuration sections
        base_agent_config = data.get('base_agent', {})
        agent_types = data.get('agent_types', {})

        for agent_name, agent_config in data.get('agents', {}).items():
            # Step 1: Start with base agent config
            merged_query_body = base_agent_config.copy()

            # Step 2: Merge agent type defaults
            agent_type = agent_config.get('type', 'REST_API')
            type_config = agent_types.get(agent_type, {})
            merged_query_body.update(type_config)

            # Step 3: Merge agent-specific query_body (overrides)
            agent_query_body = agent_config.get('query_body', {})
            merged_query_body.update(agent_query_body)

            # Create AgentConfig instance
            config = AgentConfig(
                agent_name=agent_name,
                agent_type=agent_type,
                api_key="",  # Set via environment
                api_endpoint=agent_config.get('endpoint', ''),
                auth_header_name=agent_config.get('auth_header', base_agent_config.get('auth_header', 'Authorization')),
                auth_prefix=agent_config.get('auth_prefix', base_agent_config.get('auth_prefix', 'Bearer')),
                default_params=merged_query_body
            )

            self._agent_configs[agent_name] = config

    @property
    def agent_marketplace(self) -> Dict[str, str]:
        """
        Get marketplace of available agents.

        Returns:
            Dict mapping agent name to agent type
            Example: {"BOCHA": "REST_API", "XUNFEI": "LLM_SEARCH", ...}
        """
        marketplace = {}
        for agent_name, config in self._agent_configs.items():
            marketplace[agent_name] = config.agent_type
        return marketplace

    @property
    def available_agents(self) -> Dict[str, str]:
        """Alias for agent_marketplace for convenience"""
        return self.agent_marketplace

    def create_agent(self, agent_name: str, api_key: str = None) -> SearchAgent:
        """
        Create and initialize an agent instance.

        Process:
        1. Get agent configuration from YAML
        2. Look up agent class from registry
        3. Set API key (from parameter or environment)
        4. Initialize agent with config
        5. Agent creates and maintains RequestSchema instance during __init__

        Args:
            agent_name: Name of agent to create (e.g., "BOCHA", "XUNFEI")
            api_key: API key for the agent (if not provided, assumes environment setup)

        Returns:
            Initialized SearchAgent instance with maintained RequestSchema

        Raises:
            KeyError: If agent not found in configuration
            KeyError: If agent not implemented in registry
            ValueError: If no API key provided and agent has no default
        """
        # Get configuration for this agent
        if agent_name not in self._agent_configs:
            available = ", ".join(self._agent_configs.keys())
            raise KeyError(
                f"Agent '{agent_name}' not found in configuration. "
                f"Available agents: {available}"
            )

        config = self._agent_configs[agent_name]

        # Check if agent is implemented
        if agent_name not in self._AGENT_REGISTRY:
            available = ", ".join(self._AGENT_REGISTRY.keys())
            raise KeyError(
                f"Agent '{agent_name}' is not implemented. "
                f"Implemented agents: {available}"
            )

        # Set API key if provided
        if api_key:
            config.api_key = api_key
        elif not config.api_key:
            # Warn if no default config provided
            import warnings
            warnings.warn(
                f"No API key provided for agent '{agent_name}' and no default found. "
                f"Agent initialization may fail at runtime.",
                UserWarning
            )

        # Get agent class and instantiate
        agent_class = self._AGENT_REGISTRY[agent_name]
        agent = agent_class(config)

        return agent

    def get_agent_config(self, agent_name: str) -> AgentConfig:
        """
        Get configuration for a specific agent.

        Args:
            agent_name: Name of the agent

        Returns:
            AgentConfig instance

        Raises:
            KeyError: If agent not found
        """
        if agent_name not in self._agent_configs:
            available = ", ".join(self._agent_configs.keys())
            raise KeyError(
                f"Agent '{agent_name}' not found. "
                f"Available: {available}"
            )
        return self._agent_configs[agent_name]

    def get_all_configs(self) -> Dict[str, AgentConfig]:
        """
        Get all agent configurations.

        Returns:
            Dict mapping agent names to their configurations
        """
        return self._agent_configs.copy()

    def register_agent(self, agent_name: str, agent_class: Type[SearchAgent]) -> None:
        """
        Register a new agent class.

        Allows dynamic registration of new agents at runtime.

        Args:
            agent_name: Name of the agent (e.g., "XUNFEI")
            agent_class: Agent class (must inherit from SearchAgent)

        Raises:
            TypeError: If agent_class doesn't inherit from SearchAgent
        """
        if not issubclass(agent_class, SearchAgent):
            raise TypeError(
                f"{agent_class.__name__} must inherit from SearchAgent"
            )
        self._AGENT_REGISTRY[agent_name] = agent_class

    def __repr__(self) -> str:
        """String representation of AgentManager"""
        marketplace_str = ", ".join(self.agent_marketplace.keys())
        return f"AgentManager(agents=[{marketplace_str}])"


# Global agent manager instance
_agent_manager: Optional[AgentManager] = None


def get_agent_manager(config_path: str = "config/agents.yaml") -> AgentManager:
    """
    Get or create global AgentManager instance.

    Uses singleton pattern to ensure only one manager exists.

    Args:
        config_path: Path to agents.yaml

    Returns:
        AgentManager instance
    """
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentManager(config_path)
    return _agent_manager
