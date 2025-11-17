"""Core dataclass models for search items, queries, and responses"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import uuid4


@dataclass
class SearchItem:
    """
    Represents a single search result across all sources.

    This dataclass captures the normalized output from any search agent
    (XUNFEI, BOCHA, HUNYUAN, QIANFAN, META, TWITTER).
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    title: str
    content: str
    source_url: str
    source_name: str
    source_type: str  # "XUNFEI" | "BOCHA" | "HUNYUAN" | "QIANFAN" | "META" | "TWITTER"
    timestamp: datetime

    # Optional fields
    category: Optional[str] = None
    key_entities: Optional[List[str]] = None
    relevance_score: Optional[float] = None
    significance: Optional[str] = None  # "高/中/低" for relevance level

    # Source-specific metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Query reference (NOT cascade - just metadata)
    query_id: Optional[str] = None
    topic_tags: List[str] = field(default_factory=list)

    # Internal tracking
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def normalized_timestamp(self) -> str:
        """ISO 8601 format for uniform storage"""
        return self.timestamp.isoformat()


@dataclass
class QueryRequest:
    """
    Encapsulates a single search query with all parameters.

    This dataclass aggregates all query configuration, from core search
    content to API-specific overrides, providing a unified interface
    for the entire pipeline.
    """
    # Identification
    query_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)

    # Core query content
    query_fields: List[str] = field(default_factory=list)  # ["自动驾驶", "具身智能"]
    query_topics: List[str] = field(default_factory=list)  # ["特斯拉FSD", "人形机器人"]
    source_agents: List[str] = field(default_factory=list)  # ["XUNFEI", "BOCHA"]

    # Time filtering (unified across all APIs)
    days_back: int = 7
    time_filter: str = "oneWeek"  # Explicit BOCHA format

    # Result limiting (unified)
    max_results: int = 10
    min_relevance_score: float = 0.0

    # Output configuration
    include_ai_summary: bool = True
    include_raw_response: bool = False
    exclude_duplicates: bool = True
    language: str = "zh"

    # API-specific overrides (for fine-grained control)
    api_specific_params: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # Example: {
    #   "XUNFEI": {"temperature": 0.3, "max_tokens": 4000},
    #   "QIANFAN": {"model": "deepseek-r1", "enable_reasoning": True},
    #   "META": {"scope": "webpage"}
    # }

    def get_api_param(self, agent_name: str, param_name: str, default: Any = None) -> Any:
        """Get API-specific parameter with fallback to default"""
        if agent_name in self.api_specific_params:
            return self.api_specific_params[agent_name].get(param_name, default)
        return default


@dataclass
class QueryResponse:
    """
    Contains results from a single agent's search.

    This dataclass represents the response from executing a QueryRequest
    against a single search agent. It includes both the results and
    metadata about the execution.

    Note: response_id is INDEPENDENT from query_id (no cascade relation).
    """
    # Identification - NO foreign key relationship
    response_id: str = field(default_factory=lambda: str(uuid4()))
    agent_name: str = ""
    query_id: str = ""  # Just a reference, not a foreign key
    timestamp: datetime = field(default_factory=datetime.now)

    # Results
    items: List[SearchItem] = field(default_factory=list)
    total_estimated: Optional[int] = None  # For BOCHA "totalEstimatedMatches"

    # Metadata
    success: bool = True
    error_message: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None  # If include_raw_response=True

    # Performance metrics
    execution_time_ms: int = 0
    tokens_used: Optional[int] = None  # For QIANFAN usage tracking

    # Status tracking
    budget_consumed: float = 0.0
    status: str = "completed"  # "completed" | "partial" | "failed" | "quota_exceeded"

    # Internal tracking
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def success_rate(self) -> float:
        """Percentage of expected results obtained"""
        if self.total_estimated and self.total_estimated > 0:
            return min(1.0, len(self.items) / self.total_estimated)
        return 1.0 if self.success else 0.0

    @property
    def items_count(self) -> int:
        """Number of items returned"""
        return len(self.items)
