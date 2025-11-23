"""Data model definitions for data manager

Three core models with cascade relationships:
- RequestModel: Complete raw API request and response log
- QueryModel: Structured query info (associated with RequestModel)
- ResponseItem: Single search result (associated with QueryModel)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4
from enum import Enum


class DataModelType(Enum):
    """Available data models"""
    REQUEST = "request_model"
    QUERY = "query_model"
    RESPONSE_ITEM = "response_item"


@dataclass
class RequestModel:
    """
    Complete raw API request and response log.

    Captures the full request sent to an agent's API and the raw response received.
    Serves as the root record for audit trail and debugging.
    """
    # Identification
    request_id: str = field(default_factory=lambda: str(uuid4()))
    agent_name: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    # Request details (complete raw API request)
    url: str = ""
    method: str = "POST"
    headers: Dict[str, str] = field(default_factory=dict)
    body: Dict[str, Any] = field(default_factory=dict)

    # Response details (complete raw API response)
    raw_response: Optional[Dict[str, Any]] = None
    http_status: int = 0
    response_type: str = "real_call"  # "real_call" | "cached_response" (from SimuRequest)

    # Execution metadata
    execution_time_ms: int = 0
    success: bool = True
    error_message: Optional[str] = None

    # Internal tracking
    created_at: datetime = field(default_factory=datetime.now)

    def __hash__(self):
        """Allow use as dict key"""
        return hash(self.request_id)


@dataclass
class QueryModel:
    """
    Structured query information extracted from a request.

    Parses and normalizes query parameters across different agent APIs.
    Associated with exactly one RequestModel (cascade delete).
    """
    # Identification
    query_id: str = field(default_factory=lambda: str(uuid4()))
    request_id: str = ""  # FK to RequestModel (cascade)
    agent_name: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    # Parsed common query fields (extracted from all agent schemas)
    # Agents implement their own data_value structure to fit this model
    query_keywords: List[str] = field(default_factory=list)  # Main search terms
    query_topics: List[str] = field(default_factory=list)    # Sub-topics or focus areas

    # Time filtering (normalized across all APIs)
    days_back: Optional[int] = None
    time_filter: Optional[str] = None  # e.g., "oneWeek", "week", etc.

    # Result limiting
    max_results: Optional[int] = None
    language: Optional[str] = None

    # Agent-specific parameters (raw, as-is)
    agent_specific_params: Dict[str, Any] = field(default_factory=dict)

    # Original raw query body (for reference/debugging)
    raw_query_body: Dict[str, Any] = field(default_factory=dict)

    # Internal tracking
    created_at: datetime = field(default_factory=datetime.now)

    def __hash__(self):
        """Allow use as dict key"""
        return hash(self.query_id)


@dataclass
class ResponseItem:
    """
    Single search result item parsed from agent's response.

    Represents one normalized search result from an agent.
    Multiple ResponseItems are created from a single agent response.
    Associated with exactly one QueryModel (cascade delete).
    """
    # Identification
    item_id: str = field(default_factory=lambda: str(uuid4()))
    query_id: str = ""  # FK to QueryModel (cascade)
    agent_name: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    # Core search result fields
    title: str = ""
    content: str = ""
    source_url: str = ""
    source_name: str = ""

    # Metadata
    category: Optional[str] = None
    key_entities: List[str] = field(default_factory=list)
    relevance_score: Optional[float] = None
    significance: Optional[str] = None  # "high" | "medium" | "low"

    # Agent-specific metadata (raw)
    agent_metadata: Dict[str, Any] = field(default_factory=dict)

    # Internal tracking
    created_at: datetime = field(default_factory=datetime.now)

    def __hash__(self):
        """Allow use as dict key"""
        return hash(self.item_id)
