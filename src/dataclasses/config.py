"""Configuration dataclass for search agents

DEPRECATED: The configuration loading logic has been moved to AgentManager.
This module is kept for backward compatibility only.
New code should use src.agents.manager.AgentManager instead.
"""

import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


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

    # Request body parameters (from agents.yaml defaults)
    request_body_params: Dict[str, Any] = field(default_factory=dict)


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

    with open(config_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # Extract base agent config for auth defaults
    base_agent_config = data.get('base_agent', {})

    agents = {}

    for agent_name, agent_config in data.get('agents', {}).items():
        agent_type = agent_config.get('type', 'REST_API')

        # Get pure agent-specific query_body (only what the API needs)
        agent_query_body = agent_config.get('query_body', {})

        # Create AgentConfig instance with pure agent parameters only
        config = AgentConfig(
            agent_name=agent_name,
            agent_type=agent_type,
            api_endpoint=agent_config.get('endpoint', ''),
            auth_header_name=agent_config.get('auth_header', base_agent_config.get('auth_header', 'Authorization')),
            auth_prefix=agent_config.get('auth_prefix', base_agent_config.get('auth_prefix', 'Bearer')),
            request_body_params=agent_query_body
        )

        agents[agent_name] = config

    return agents


# Load configurations from YAML file
AGENT_CONFIGS = load_agents_from_yaml()