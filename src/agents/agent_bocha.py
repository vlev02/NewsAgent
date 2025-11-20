"""BOCHA Web Search API agent implementation"""

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


class BochaRequestSchema(RequestSchema):
    """
    BOCHA Web Search API request body schema.

    BOCHA API expects:
    - query: single keyword string
    - freshness: time filter enum
    - count: number of results (1-100)
    - summary: boolean for AI summary

    All defaults come from config/agents.yaml (BOCHA.query_body)
    """

    query: str = Field(
        default=None,
        min_length=1,
        max_length=1000,
        description="Search query keywords (1-1000 characters)"
    )

    freshness: Literal["oneDay", "oneWeek", "oneMonth", "oneYear"] = Field(
        default=None,
        description="Time filter for search results (oneDay, oneWeek, oneMonth, oneYear)"
    )

    count: int = Field(
        default=None,
        ge=1,
        le=100,
        description="Number of results to return (1-100)"
    )

    summary: bool = Field(
        default=None,
        description="Include AI-generated summary in results"
    )

    class Config:
        """Pydantic configuration"""
        extra = "allow"  # Allow additional BOCHA-specific parameters
        validate_assignment = True


class BochaAgent(SearchAgent):
    """
    Agent for BOCHA Web Search API.

    BOCHA provides a REST API for web search with optional AI summaries.
    Supports time filtering and multi-modal search.

    Configuration Pattern:
    - Receives AgentConfig with query_body defaults from agents.yaml
    - Maintains BochaRequestSchema instance for request validation
    - query_body parameters: query, freshness, count, summary, language
    """

    NAME: str = "BOCHA"

    def __init__(self, config: AgentConfig):
        super().__init__(config)

    def _get_request_schema_class(self) -> Type:
        """
        Get the RequestSchema class for BOCHA.

        Returns:
            BochaRequestSchema class
        """
        return BochaRequestSchema

    def _load_prompt_template(self) -> Optional[None]:
        """BOCHA is a REST API, not LLM-based, so no template needed"""
        return None

    def build_query(self, request: QueryRequest) -> str:
        """
        Build simple keyword query for BOCHA.

        Args:
            request: QueryRequest with search parameters

        Returns:
            Keyword query string
        """
        return build_query_string(request.query_fields, request.query_topics, separator=" ")

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "agent_name": self.config.agent_name,
            "is_available": True
        }

    def call_api(self,
                 query: Union[str, Dict[str, Any]],
                 request: QueryRequest) -> Dict[str, Any]:
        """
        Pure API call - only makes HTTP request and returns formatted response.

        This is the fundamental operation that only calls the API without any
        post-processing. Uses handle_api_request() utility for centralized
        request handling with caching, formatting, and response interception.

        Args:
            query: Keyword query string
            request: Original QueryRequest (for building API body)

        Returns:
            Formatted response dict (via dataclasses.asdict() or cached)

        Raises:
            requests.RequestException: If API call fails
            ValueError: If request body fails schema validation
        """
        # Get API-specific time filter
        time_filter = get_api_time_filter(request.days_back, self.config.agent_name)

        # Build request body
        body = {
            "query": query,
            "freshness": time_filter,
            "count": request.max_results,
            "summary": request.include_ai_summary
        }

        # Merge API-specific params
        api_params = request.get_api_param(self.config.agent_name, None) or {}
        body.update(api_params)

        # Validate request body against BOCHA schema
        # This ensures the body conforms to BOCHA API requirements
        validated_schema = BochaRequestSchema(**body)
        validated_body = validated_schema.validate_and_get_dict()

        # Use centralized request handler with all request parameters
        # No lambda wrapper - all HTTP parameters passed directly
        return handle_api_request(
            agent_name=self.config.agent_name,
            url=self.config.api_endpoint,
            method="POST",
            description="web_search",
            json_body=validated_body,
            headers=self.get_header_dict(),
            timeout=120,
            query_request=request
        )

    def submit_request(self,
                      query: Union[str, Dict[str, Any]],
                      request: QueryRequest) -> QueryResponse:
        """
        Execute BOCHA web search and return parsed QueryResponse.

        This method:
        1. Calls the pure API via call_api()
        2. Parses raw response into SearchItem list
        3. Builds QueryResponse with metadata

        Args:
            query: Keyword query string
            request: Original QueryRequest

        Returns:
            QueryResponse with parsed results
        """
        try:
            # Step 1: Call pure API
            raw_response = self.call_api(query, request)

            # Step 2: Parse items from response
            items = self.parse_response(raw_response)

            # Step 3: Extract metadata
            total_estimated = None
            if 'webPages' in raw_response:
                total_estimated = raw_response['webPages'].get('totalEstimatedMatches')

            # Step 4: Build QueryResponse
            query_response = QueryResponse(
                items=items,
                total_estimated=total_estimated,
                success=True,
                status="completed"
            )

            # Step 5: Store raw response if requested
            if request.include_raw_response:
                query_response.raw_response = raw_response

            return query_response

        except Exception as e:
            return QueryResponse(
                items=[],
                success=False,
                error_message=f"API request failed: {str(e)}",
                status="failed"
            )

    def parse_response(self, raw_response: Dict[str, Any]) -> List[SearchItem]:
        """
        Parse BOCHA response into SearchItem list.

        Args:
            raw_response: Raw API response

        Returns:
            List of SearchItem objects
        """
        items = []

        # Handle BOCHA response format
        web_pages = raw_response.get('webPages', {})
        results = web_pages.get('value', [])

        for idx, result in enumerate(results):
            try:
                item = SearchItem(
                    id=result.get('id', str(idx)),
                    title=result.get('name', ''),
                    content=result.get('snippet', ''),
                    source_url=result.get('url', ''),
                    source_name=result.get('siteName', ''),
                    source_type="BOCHA",
                    timestamp=self.normalize_timestamp(result.get('datePublished', '')),
                    category=None,
                    key_entities=None,
                    relevance_score=None,
                    significance=None,
                    metadata={
                        'site_icon': result.get('siteIcon'),
                        'summary': result.get('summary')
                    },
                    query_id=None,
                    topic_tags=[]
                )
                items.append(item)
            except Exception as e:
                # Skip items that fail to parse
                continue

        return items

    def normalize_timestamp(self, timestamp_str: str) -> datetime:
        """
        Convert BOCHA timestamp to datetime.

        BOCHA returns ISO 8601 format: 2025-01-01T00:00:00

        Args:
            timestamp_str: ISO 8601 timestamp string

        Returns:
            Normalized datetime object
        """
        if not timestamp_str:
            return datetime.now()

        try:
            # Parse ISO 8601
            if 'T' in timestamp_str:
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                # Parse date only
                return datetime.strptime(timestamp_str, '%Y-%m-%d')
        except (ValueError, AttributeError):
            return datetime.now()
