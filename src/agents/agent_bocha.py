"""BOCHA Web Search API agent implementation"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Union, Literal

from pydantic import Field

from .config import AgentConfig
from src.debug_config import DebugConfig
from .base import SearchAgent
from .request_schema import RequestSchema


class BochaRequestSchema(RequestSchema):
    """
    BOCHA Web Search API request body schema.

    BOCHA API expects:
    - query: single keyword string
    - freshness: time filter enum
    - count: number of results (1-100)
    - summary: boolean for AI summary

    All defaults come from config/agents.yaml (BOCHA request_body_params)
    """

    query: str = Field(
        min_length=1,
        max_length=1000,
        description="Search query keywords (1-1000 characters)"
    )

    freshness: Literal["oneDay", "oneWeek", "oneMonth", "oneYear"] = Field(
        description="Time filter for search results (oneDay, oneWeek, oneMonth, oneYear)"
    )

    count: int = Field(
        ge=1,
        le=100,
        description="Number of results to return (1-100)"
    )

    summary: bool = Field(
        description="Include AI-generated summary in results"
    )


class BochaAgent(SearchAgent):
    """
    Agent for BOCHA Web Search API.

    BOCHA provides a REST API for web search with optional AI summaries.
    Supports time filtering and multi-modal search.

    Configuration Pattern:
    - Receives AgentConfig with query_body defaults from agents.yaml
    - Maintains BochaRequestSchema instance for request validation
    - query_body parameters: query, freshness, count, summary, language

    API Keys Required:
    - BOCHA_API_KEY: The API key for BOCHA service
    """

    NAME: str = "BOCHA"
    api_keys: List[str] = ["BOCHA_API_KEY"]

    def __init__(self, config: AgentConfig):
        super().__init__(config)

    def get_header_dict(self) -> Dict[str, str]:
        """
        Get HTTP headers for BOCHA API requests.

        Extracts the BOCHA_API_KEY from api_keys_dict.

        Returns:
            Dict with Authorization header and content type
        """
        api_key = self.api_keys_dict.get("BOCHA_API_KEY", "")
        headers = {
            self.auth_header_name: f"{self.auth_prefix} {api_key}",
            "Content-Type": "application/json"
        }
        return headers

    def _get_request_schema_class(self) -> Type:
        """
        Get the RequestSchema class for BOCHA.

        Returns:
            BochaRequestSchema class
        """
        return BochaRequestSchema
