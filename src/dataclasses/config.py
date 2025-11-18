"""Configuration dataclass for search agents"""

import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class AgentConfig:
    """
    Configuration for a specific search agent.

    This dataclass defines all necessary configuration for initializing
    and running a search agent, including authentication, rate limiting,
    capabilities, and default parameters.
    """
    # Identity
    agent_name: str
    agent_type: str  # "LLM_SEARCH" | "REST_API" | "SOCIAL_MEDIA"

    # Authentication
    api_key: str
    api_endpoint: str
    auth_header_name: str = "Authorization"
    auth_prefix: str = "Bearer"

    # Search capabilities
    supports_time_filter: bool = True
    time_filter_param_name: Optional[str] = "freshness"  # "freshness", "search_recency_filter", "start_time", or None
    time_filter_values: Dict[int, str] = field(default_factory=dict)
    # Example: {1: "oneDay", 7: "oneWeek", 30: "oneMonth"}

    supports_ai_summary: bool = True
    summary_param_name: Optional[str] = None  # "summary", None (implicit)

    supports_streaming: bool = False
    streaming_format: Optional[str] = None  # "sse", None

    # Response structure
    response_format: str = "openai"  # "openai" | "bocha" | "twitter" | "meta"
    needs_json_extraction: bool = False  # For XUNFEI/HUNYUAN

    # Model/version info
    default_model: Optional[str] = None
    available_models: List[str] = field(default_factory=list)

    # Default parameters for API calls
    default_params: Dict[str, Any] = field(default_factory=dict)


def load_agents_from_yaml(yaml_path: str = "config/agents.yaml") -> Dict[str, AgentConfig]:
    """
    Load agent configurations from YAML file.

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

    agents = {}

    for agent_name, config in data.get('agents', {}).items():
        # Map YAML structure to AgentConfig fields
        agent_type = config.get('type', 'REST_API')
        endpoint = config.get('endpoint', '')

        # Extract capabilities
        capabilities = config.get('capabilities', {})

        # Extract defaults
        defaults = config.get('defaults', {})

        # Determine auth header based on agent
        if agent_name == "QIANFAN":
            auth_header = "X-Appbuilder-Authorization"
        else:
            auth_header = "Authorization"

        # Build time filter mapping based on agent
        time_filter_values = {}
        if agent_name == "BOCHA":
            time_filter_values = {
                1: "oneDay",
                7: "oneWeek",
                30: "oneMonth",
                365: "oneYear"
            }
        elif agent_name == "QIANFAN":
            time_filter_values = {
                1: "week",
                7: "week",
                30: "month",
                365: "semiyear"
            }

        # Determine time filter param name
        if agent_name == "BOCHA":
            time_filter_param = "freshness"
        elif agent_name == "QIANFAN":
            time_filter_param = "search_recency_filter"
        elif agent_name == "TWITTER":
            time_filter_param = "start_time"
        else:
            time_filter_param = None  # Embedded in prompt for LLM agents

        # Determine response format
        if agent_name == "BOCHA":
            response_format = "bocha"
        elif agent_name == "META":
            response_format = "meta"
        elif agent_name == "TWITTER":
            response_format = "twitter"
        else:
            response_format = "openai"

        # Extract model info
        default_model = defaults.get('model', None)

        # Create AgentConfig instance
        agent_config = AgentConfig(
            agent_name=agent_name,
            agent_type=agent_type,
            api_key="",  # Set via environment
            api_endpoint=endpoint,
            auth_header_name=auth_header,
            auth_prefix="Bearer",
            supports_time_filter=capabilities.get('supports_time_filter', True),
            time_filter_param_name=time_filter_param,
            time_filter_values=time_filter_values,
            supports_ai_summary=capabilities.get('supports_ai_summary', True),
            summary_param_name="summary" if agent_name == "BOCHA" else None,
            supports_streaming=capabilities.get('supports_streaming', False),
            response_format=response_format,
            needs_json_extraction=capabilities.get('needs_json_extraction', False),
            default_model=default_model,
            available_models=[],  # Could extract from YAML if needed
            default_params=defaults
        )

        agents[agent_name] = agent_config

    return agents


# Load configurations from YAML file
try:
    AGENT_CONFIGS = load_agents_from_yaml()

    # Create individual config variables for backward compatibility
    XUNFEI_CONFIG = AGENT_CONFIGS.get("XUNFEI")
    BOCHA_CONFIG = AGENT_CONFIGS.get("BOCHA")
    HUNYUAN_CONFIG = AGENT_CONFIGS.get("HUNYUAN")
    QIANFAN_CONFIG = AGENT_CONFIGS.get("QIANFAN")
    META_CONFIG = AGENT_CONFIGS.get("META")
    TWITTER_CONFIG = AGENT_CONFIGS.get("TWITTER")

except FileNotFoundError as e:
    print(f"Warning: Could not load agents.yaml: {e}")
    print("Using empty configuration. Please ensure config/agents.yaml exists.")
    AGENT_CONFIGS = {}
    XUNFEI_CONFIG = None
    BOCHA_CONFIG = None
    HUNYUAN_CONFIG = None
    QIANFAN_CONFIG = None
    META_CONFIG = None
    TWITTER_CONFIG = None
