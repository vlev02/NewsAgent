"""Configuration dataclass for search agents"""

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

    # Rate limiting & budget
    requests_per_minute: Optional[int] = None
    max_calls_per_day: Optional[int] = None
    daily_quota_reset_time: Optional[str] = "00:00"  # UTC time
    estimated_cost_per_request: float = 0.0
    max_daily_budget: Optional[float] = None

    # Search capabilities
    supports_time_filter: bool = True
    time_filter_param_name: str = "freshness"  # "freshness", "search_recency_filter", "start_time"
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


# Pre-defined configurations for known agents
XUNFEI_CONFIG = AgentConfig(
    agent_name="XUNFEI",
    agent_type="LLM_SEARCH",
    api_key="",  # Set via environment
    api_endpoint="https://spark-api-open.xf-yun.com/v1/chat/completions",
    auth_header_name="Authorization",
    auth_prefix="Bearer",
    requests_per_minute=10,
    supports_time_filter=True,
    time_filter_param_name=None,  # Embedded in prompt
    time_filter_values={},
    supports_ai_summary=True,
    supports_streaming=False,
    response_format="openai",
    needs_json_extraction=True,
    default_model="4.0Ultra",
    available_models=["4.0Ultra", "4.0Max"],
    default_params={
        "temperature": 0.3,
        "max_tokens": 4000,
        "search_mode": "deep"
    }
)

BOCHA_CONFIG = AgentConfig(
    agent_name="BOCHA",
    agent_type="REST_API",
    api_key="",  # Set via environment
    api_endpoint="https://api.bochaai.com/v1/web-search",
    auth_header_name="Authorization",
    auth_prefix="Bearer",
    requests_per_minute=30,
    supports_time_filter=True,
    time_filter_param_name="freshness",
    time_filter_values={
        1: "oneDay",
        7: "oneWeek",
        30: "oneMonth",
        365: "oneYear"
    },
    supports_ai_summary=True,
    summary_param_name="summary",
    supports_streaming=False,
    response_format="bocha",
    needs_json_extraction=False,
    default_params={
        "count": 10,
        "summary": True
    }
)

HUNYUAN_CONFIG = AgentConfig(
    agent_name="HUNYUAN",
    agent_type="LLM_SEARCH",
    api_key="",  # Set via environment
    api_endpoint="https://hunyuan.tencentcloudapi.com",
    auth_header_name="Authorization",
    auth_prefix="Bearer",
    requests_per_minute=10,
    supports_time_filter=True,
    time_filter_param_name=None,  # Embedded in prompt
    supports_ai_summary=True,
    supports_streaming=False,
    response_format="openai",
    needs_json_extraction=True,
    default_model="hunyuan-turbo",
    available_models=["hunyuan-turbo", "hunyuan-standard"],
    default_params={
        "temperature": 0.3,
        "enable_enhancement": True,
        "search_info": True
    }
)

QIANFAN_CONFIG = AgentConfig(
    agent_name="QIANFAN",
    agent_type="LLM_SEARCH",
    api_key="",  # Set via environment
    api_endpoint="https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/",
    auth_header_name="X-Appbuilder-Authorization",
    auth_prefix="Bearer",
    requests_per_minute=10,
    max_calls_per_day=100,
    estimated_cost_per_request=0.0,
    supports_time_filter=True,
    time_filter_param_name="search_recency_filter",
    time_filter_values={
        1: "week",  # Baidu doesn't have "day", use "week"
        7: "week",
        30: "month",
        365: "semiyear"
    },
    supports_ai_summary=True,
    supports_streaming=False,
    response_format="openai",
    needs_json_extraction=False,
    default_model="deepseek-r1",
    available_models=["deepseek-r1", "ernie-3.5-8k", "ernie-4.0"],
    default_params={
        "search_source": "baidu_search_v2",
        "enable_deep_search": False,
        "enable_reasoning": True,
        "temperature": 1e-10,
        "top_p": 1e-10,
        "max_completion_tokens": 20480
    }
)

META_CONFIG = AgentConfig(
    agent_name="META",
    agent_type="REST_API",
    api_key="",  # Set via environment
    api_endpoint="https://api.metaso.cn/search",
    auth_header_name="Authorization",
    auth_prefix="Bearer",
    requests_per_minute=30,
    supports_time_filter=True,
    time_filter_param_name=None,  # Embedded in query
    supports_ai_summary=False,
    supports_streaming=False,
    response_format="meta",
    needs_json_extraction=False,
    default_params={
        "scope": "webpage",
        "size": 10,
        "includeRawContent": False,
        "includeSummary": False
    }
)

TWITTER_CONFIG = AgentConfig(
    agent_name="TWITTER",
    agent_type="SOCIAL_MEDIA",
    api_key="",  # Set via environment (Bearer token)
    api_endpoint="https://api.twitter.com/2",
    auth_header_name="Authorization",
    auth_prefix="Bearer",
    requests_per_minute=15,
    supports_time_filter=True,
    time_filter_param_name="start_time",
    supports_ai_summary=False,
    supports_streaming=False,
    response_format="twitter",
    needs_json_extraction=False,
    default_params={
        "sort_order": "recency",
        "max_results": 10
    }
)

# Registry of all known agent configurations
AGENT_CONFIGS = {
    "XUNFEI": XUNFEI_CONFIG,
    "BOCHA": BOCHA_CONFIG,
    "HUNYUAN": HUNYUAN_CONFIG,
    "QIANFAN": QIANFAN_CONFIG,
    "META": META_CONFIG,
    "TWITTER": TWITTER_CONFIG,
}
