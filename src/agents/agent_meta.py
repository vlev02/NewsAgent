"""MetaSo Search API agent implementation"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Union, Literal

from pydantic import Field

from src.dataclasses import AgentConfig, QueryRequest, QueryResponse, SearchItem
from src.utils import get_api_time_filter, get_time_description, build_query_string
from src.decorators import handle_api_request
from src.debug_config import DebugConfig
from .base import SearchAgent
from .request_schema import RequestSchema


class MetaRequestSchema(RequestSchema):
    """
    MetaSo Search API request body schema.

    MetaSo API expects:
    - q: search query string
    - scope: search scope (webpage, news, etc.)
    - size: number of results
    - includeSummary: whether to include AI summary
    - includeRawContent: whether to include raw content
    - conciseSnippet: whether to use concise snippets

    All defaults come from config/agents.yaml (META request_body_params)
    """

    q: str = Field(
        min_length=1,
        max_length=1000,
        description="Search query keywords (1-1000 characters)"
    )

    scope: Literal["webpage", "news", "scholar", "all"] = Field(
        default="webpage",
        description="Search scope (webpage, news, scholar, all)"
    )

    size: int = Field(
        ge=1,
        le=100,
        default=10,
        description="Number of results to return (1-100)"
    )

    includeSummary: bool = Field(
        default=False,
        description="Include AI-generated summary in results"
    )

    includeRawContent: bool = Field(
        default=True,
        description="Include raw content in results"
    )

    conciseSnippet: bool = Field(
        default=True,
        description="Use concise snippets for results"
    )


class MetaAgent(SearchAgent):
    """
    Agent for MetaSo Search API.

    MetaSo provides a REST API for web search with optional AI summaries.
    Supports scope filtering (webpage, news, scholar) and flexible result formatting.

    Configuration Pattern:
    - Receives AgentConfig with query_body defaults from agents.yaml
    - Maintains MetaRequestSchema instance for request validation
    - query_body parameters: q, scope, size, includeSummary, includeRawContent, conciseSnippet

    API Keys Required:
    - META_API_KEY: The API key for MetaSo service
    """

    NAME: str = "META"
    api_keys: List[str] = ["META_API_KEY"]

    def __init__(self, config: AgentConfig):
        super().__init__(config)

    def get_header_dict(self) -> Dict[str, str]:
        """
        Get HTTP headers for MetaSo API requests.

        Extracts the META_API_KEY from api_keys_dict.

        Returns:
            Dict with Authorization header and content type
        """
        api_key = self.api_keys_dict.get("META_API_KEY", "")
        headers = {
            self.auth_header_name: f"{self.auth_prefix} {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        return headers

    def _get_request_schema_class(self) -> Type:
        """
        Get the RequestSchema class for META.

        Returns:
            MetaRequestSchema class
        """
        return MetaRequestSchema
