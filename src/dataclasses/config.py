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

    # Extract configuration sections
    base_agent_config = data.get('base_agent', {})
    agent_types = data.get('agent_types', {})

    agents = {}

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
            api_key="",  # Set via environment by SchedulerSettings
            api_endpoint=agent_config.get('endpoint', ''),
            auth_header_name=agent_config.get('auth_header', base_agent_config.get('auth_header', 'Authorization')),
            auth_prefix=agent_config.get('auth_prefix', base_agent_config.get('auth_prefix', 'Bearer')),
            default_params=merged_query_body
        )

        agents[agent_name] = config

    return agents


# Load configurations from YAML file
AGENT_CONFIGS = load_agents_from_yaml()