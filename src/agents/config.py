"""Configuration dataclass for search agents.

This module centralizes agent configuration structures within the agents
package so AgentManager and agent implementations can share a single source
of truth.

Legacy consumers that import AgentConfig from src.dataclasses continue to
work via a compatibility shim in src/dataclasses/config.py.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any

import yaml


@dataclass
class AgentConfig:
    """
    Configuration for a specific search agent.

    All configuration is loaded from config/agents.yaml.
    No hardcoded defaults should exist in code.

    API Key Management:
    - api_keys: Dict[str, str] - Dictionary of all API keys required by agent
      Example: {"BOCHA_API_KEY": "...", "XUNFEI_APPID": "...", "XUNFEI_APIKey": "..."}
    - Agent declares required keys via api_keys class attribute (List[str])
    - AgentManager acquires and injects keys into config.api_keys during create_agent()

    Template Configuration (for LLM_SEARCH agents):
    - template_config: Dict[str, Any] - Template path and variables
    - template_vars: Dict[str, Any] - Template variables for Jinja2 rendering
    - Both are loaded from agents.yaml and can be modified at runtime
    """

    # Identity
    agent_name: str
    agent_type: str  # "LLM_SEARCH" | "REST_API" | "SOCIAL_MEDIA"

    # Endpoint
    api_endpoint: str = ""
    auth_header_name: str = "Authorization"
    auth_prefix: str = "Bearer"

    # API Keys Management
    api_keys: Dict[str, str] = field(default_factory=dict)  # All required keys for the agent

    # Request body parameters (from agents.yaml query_body)
    request_body_params: Dict[str, Any] = field(default_factory=dict)

    # Template configuration (for LLM_SEARCH agents - from agents.yaml template section)
    template_config: Dict[str, Any] = field(default_factory=dict)  # Template path, name, etc.
    template_vars: Dict[str, Any] = field(default_factory=dict)  # Template variables for rendering


def load_agents_from_yaml(yaml_path: str = "config/agents.yaml") -> Dict[str, AgentConfig]:
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

    Args:
        yaml_path: Path to agents.yaml file

    Returns:
        Dict mapping agent names to AgentConfig instances
    """

    # Resolve path relative to project root
    project_root = Path(__file__).parent.parent.parent
    config_file = project_root / yaml_path

    if not config_file.exists():
        raise FileNotFoundError(f"Agent config file not found: {config_file}")

    with open(config_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Extract base agent config for auth defaults
    base_agent_config = data.get("base_agent", {})

    agents: Dict[str, AgentConfig] = {}

    for agent_name, agent_config in data.get("agents", {}).items():
        agent_type = agent_config.get("type", "REST_API")

        # Get pure agent-specific query_body (only what the API needs)
        agent_query_body = agent_config.get("query_body", {})

        # Create AgentConfig instance with pure agent parameters only
        config = AgentConfig(
            agent_name=agent_name,
            agent_type=agent_type,
            api_endpoint=agent_config.get("endpoint", ""),
            auth_header_name=agent_config.get("auth_header", base_agent_config.get("auth_header", "Authorization")),
            auth_prefix=agent_config.get("auth_prefix", base_agent_config.get("auth_prefix", "Bearer")),
            request_body_params=agent_query_body,
        )

        agents[agent_name] = config

    return agents


# Legacy global (not used by AgentManager but preserved for compatibility)
AGENT_CONFIGS = load_agents_from_yaml()


__all__ = ["AgentConfig", "load_agents_from_yaml", "AGENT_CONFIGS"]
