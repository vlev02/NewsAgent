"""Agent Manager - Centralized agent instantiation and lifecycle management"""

import yaml
import importlib
import os
from pathlib import Path
from typing import Dict, Any, Type, Optional

from .config import AgentConfig
from src.agents.base import SearchAgent


def _auto_load_agents():
    """
    Automatically load all agent modules from the agents directory.

    This function scans the agents directory for all agent_*.py files and imports them.
    This ensures all SearchAgent subclasses are registered before discovery.

    No manual imports needed - just create a new agent_xxx.py file and it's automatically loaded.
    """
    agents_dir = Path(__file__).parent

    # Find all agent_*.py files in the agents directory
    for agent_file in agents_dir.glob("agent_*.py"):
        module_name = agent_file.stem  # e.g., "agent_bocha"

        try:
            # Dynamically import the module
            full_module_name = f"src.agents.{module_name}"
            importlib.import_module(full_module_name)
        except (ImportError, Exception):
            # Silently skip agents that fail to import (e.g., dependencies not installed)
            pass


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

    @classmethod
    def _discover_agents(cls) -> Dict[str, Type[SearchAgent]]:
        """
        Auto-discover all SearchAgent subclasses and build registry by their NAME property.

        This method recursively finds all classes that inherit from SearchAgent,
        eliminating the need for manual registration lists.

        Each agent class must have a NAME class attribute for identification.

        Returns:
            Dict mapping agent NAME to agent class
        """
        # Auto-load all agent modules from the agents directory
        _auto_load_agents()

        registry = {}

        def get_all_subclasses(base_class):
            """Recursively get all subclasses of a base class"""
            all_subclasses = []
            for subclass in base_class.__subclasses__():
                all_subclasses.append(subclass)
                all_subclasses.extend(get_all_subclasses(subclass))
            return all_subclasses

        # Get all SearchAgent subclasses
        all_agents = get_all_subclasses(SearchAgent)

        # Index by NAME property
        for agent_class in all_agents:
            if hasattr(agent_class, 'NAME') and agent_class.NAME:
                registry[agent_class.NAME] = agent_class

        return registry

    def __init__(self, config_path: str = "config/agents.yaml"):
        """
        Initialize AgentManager.

        Args:
            config_path: Path to agents.yaml configuration file
        """
        self.config_path = config_path
        self._agent_configs: Dict[str, AgentConfig] = {}  # Configurations from YAML + env
        self._agent_instances: Dict[str, SearchAgent] = {}  # Cached agent instances
        self.all_keys: Dict[str, str] = {}  # API keys storage (name -> value)
        self._agent_registry: Dict[str, Type[SearchAgent]] = self._discover_agents()
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

        # Extract base agent config for auth defaults
        base_agent_config = data.get('base_agent', {})

        for agent_name, agent_config in data.get('agents', {}).items():
            agent_type = agent_config.get('type', 'REST_API')

            # Separate query_body (API request params) from template config
            agent_query_body = agent_config.get('query_body', {})
            agent_template_config = agent_config.get('template', {})
            agent_template_vars = agent_config.get('template_vars', {})

            # Create AgentConfig instance with proper separation of concerns
            config = AgentConfig(
                agent_name=agent_name,
                agent_type=agent_type,
                api_endpoint=agent_config.get('endpoint', ''),
                auth_header_name=agent_config.get('auth_header', base_agent_config.get('auth_header', 'Authorization')),
                auth_prefix=agent_config.get('auth_prefix', base_agent_config.get('auth_prefix', 'Bearer')),
                request_body_params=agent_query_body,
                template_config=agent_template_config,
                template_vars=agent_template_vars
            )

            self._agent_configs[agent_name] = config

    @property
    def agent_marketplace(self) -> Dict[str, str]:
        """
        Get marketplace of available (implemented) agents.

        Returns only agents that are actually implemented (in _agent_registry).

        Returns:
            Dict mapping agent name to agent type
            Example: {"BOCHA": "REST_API"}
        """
        marketplace = {}
        for agent_name in self._agent_registry.keys():
            if agent_name in self._agent_configs:
                config = self._agent_configs[agent_name]
                marketplace[agent_name] = config.agent_type
        return marketplace

    @property
    def available_agents(self) -> Dict[str, str]:
        """Alias for agent_marketplace for convenience"""
        return self.agent_marketplace

    def create_agent(self, agent_name: str) -> SearchAgent:
        """
        Create and initialize an agent instance.

        Process:
        1. Get agent configuration from YAML + env vars
        2. Check if agent is implemented in registry
        3. Acquire all required API keys from manager's all_keys or environment
        4. Inject all keys into config.api_keys dict
        5. Initialize agent with config
        6. Cache agent instance in _agent_instances
        7. Agent creates and maintains RequestSchema instance during __init__

        Args:
            agent_name: Name of agent to create (e.g., "BOCHA", "XUNFEI")

        Returns:
            Initialized SearchAgent instance with maintained RequestSchema

        Raises:
            KeyError: If agent not found in configuration
            KeyError: If agent not implemented in registry
            KeyError: If required API keys not found
        """
        # Get configuration for this agent
        if agent_name not in self._agent_configs:
            available = ", ".join(self._agent_configs.keys())
            raise KeyError(
                f"Agent '{agent_name}' not found in configuration. "
                f"Available agents: {available}"
            )

        # Check if agent is implemented
        if agent_name not in self._agent_registry:
            available = ", ".join(self._agent_registry.keys())
            raise KeyError(
                f"Agent '{agent_name}' is not implemented. "
                f"Implemented agents: {available}"
            )

        # Get agent class and acquire its required API keys
        agent_class = self._agent_registry[agent_name]

        # Create a copy of config for this instance
        config = self._agent_configs[agent_name]

        # Acquire all required API keys from manager or environment
        acquired_keys = self._acquire_agent_keys(agent_class)
        # Store all acquired keys in config.api_keys dict
        config.api_keys = acquired_keys

        # Instantiate the agent
        agent = agent_class(config)

        # Cache the agent instance
        self._agent_instances[agent_name] = agent

        return agent

    def get_agent_config(self, agent_name: str) -> AgentConfig:
        """
        Get configuration for a specific agent.

        Internal method used to retrieve agent configuration. Exposed for access
        to configuration details without creating an agent instance.

        Args:
            agent_name: Name of the agent

        Returns:
            AgentConfig instance with configuration from YAML + env vars

        Raises:
            KeyError: If agent not found in configuration
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
            Dict mapping agent names to their AgentConfig instances
        """
        return self._agent_configs.copy()

    def get_cached_agents(self) -> Dict[str, SearchAgent]:
        """
        Get all cached agent instances.

        Returns:
            Dict mapping agent names to their SearchAgent instances
            Only includes agents that have been created via create_agent()
        """
        return self._agent_instances.copy()

    def add_api_key(self, key_name: str, key_value: str) -> None:
        """
        Add an API key to the manager's key storage.

        Args:
            key_name: Name of the key (e.g., "BOCHA_API_KEY", "XUNFEI_APPID")
            key_value: The API key value
        """
        self.all_keys[key_name] = key_value

    def add_api_keys(self, keys: Dict[str, str]) -> None:
        """
        Add multiple API keys at once.

        Args:
            keys: Dict mapping key names to their values
                  Example: {"BOCHA_API_KEY": "...", "XUNFEI_APPID": "..."}
        """
        self.all_keys.update(keys)

    def _get_api_key(self, key_name: str) -> Optional[str]:
        """
        Get an API key from manager's all_keys or environment variables.

        Checks in order:
        1. Manager's all_keys dict
        2. Environment variable with same name

        Args:
            key_name: Name of the key to retrieve

        Returns:
            The API key value, or None if not found
        """
        # Check manager's all_keys first
        if key_name in self.all_keys:
            return self.all_keys[key_name]

        # Check environment variable
        key_value = os.environ.get(key_name)
        if key_value:
            # Cache it in all_keys for future use
            self.all_keys[key_name] = key_value
            return key_value

        return None

    def _acquire_agent_keys(self, agent_class: Type[SearchAgent]) -> Dict[str, str]:
        """
        Acquire all required API keys for an agent.

        Retrieves keys from manager's all_keys or environment variables.

        Args:
            agent_class: The agent class to get keys for

        Returns:
            Dict mapping key names to their values

        Raises:
            KeyError: If any required key is not found
        """
        keys = {}

        # Get required keys from agent class
        required_keys = getattr(agent_class, 'api_keys', [])

        for key_name in required_keys:
            key_value = self._get_api_key(key_name)
            if key_value is None:
                raise KeyError(
                    f"API key '{key_name}' required by {agent_class.NAME} not found. "
                    f"Add it via manager.add_api_key('{key_name}', value) "
                    f"or set environment variable {key_name}"
                )
            keys[key_name] = key_value

        return keys

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
