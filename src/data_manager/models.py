"""Data model definitions for data manager

Two core models with cascade relationships:
- RequestModel: Complete raw API request and response log
- ResponseItem: Single search result (directly associated with RequestModel)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4
from enum import Enum


class DataModelType(Enum):
    """Available data models"""
    REQUEST = "request_model"
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
class ResponseItem:
    """
    Single search result item parsed from agent's response.

    Represents one normalized search result from an agent.
    Multiple ResponseItems are created from a single agent response.
    Associated directly with a RequestModel (cascade delete).
    """
    # Identification
    item_id: str = field(default_factory=lambda: str(uuid4()))
    request_id: str = ""  # FK to RequestModel (cascade)
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
