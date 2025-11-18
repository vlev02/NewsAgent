"""BOCHA Web Search API agent implementation"""

import json
import requests
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from src.dataclasses import AgentConfig, QueryRequest, QueryResponse, SearchItem
from src.utils import get_api_time_filter, get_time_description, build_query_string
from src.decorators import fake_response_handler
from src.debug_config import DebugConfig
from .base import SearchAgent


class BochaAgent(SearchAgent):
    """
    Agent for BOCHA Web Search API.

    BOCHA provides a REST API for web search with optional AI summaries.
    Supports time filtering and multi-modal search.
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)

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

    @fake_response_handler()  # Auto-extracts: agent_name, url, description
    def call_api(self,
                 query: Union[str, Dict[str, Any]],
                 request: QueryRequest) -> Dict[str, Any]:
        """
        Pure API call - only makes HTTP request and returns raw response.

        This is the fundamental operation that only calls the API without any
        post-processing. The @fake_response_handler decorator caches the raw
        response for debugging and offline development.

        Args:
            query: Keyword query string
            request: Original QueryRequest (for building API body)

        Returns:
            Raw API response dict (status code 200)

        Raises:
            requests.RequestException: If API call fails
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

        # Make HTTP request - no error handling, no parsing
        response = requests.post(
            self.config.api_endpoint,
            json=body,
            headers=self.get_header_dict(),
            timeout=120
        )
        response.raise_for_status()

        # Return raw JSON response (no processing)
        return response.json()

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

        except requests.RequestException as e:
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
