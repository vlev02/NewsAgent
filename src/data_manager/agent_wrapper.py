"""Agent wrapper for DataManager integration

Provides a bridge between agents and the independent DataManager.
Agents inherit from this to automatically support data persistence.

Parsers (Case-Specific Extractors):
- parse_request: Extract RequestModel data from agent state
- parse_query: Extract QueryModel data from agent state
- parse_response_items: Extract ResponseItem list from API response

Usage:
    class MyAgent(SearchAgent, AgentDataWrapper):
        NAME = "MYAGENT"

        # Optional: override parse_* methods for custom parsing
        def parse_query(self, ...):
            return super().parse_query(...) + custom_fields
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class AgentDataWrapper:
    """
    Mixin class for agents to support DataManager integration.

    Provides parser methods that convert agent state into DataManager data values.

    Agents must have:
    - NAME: str (agent identifier)
    - api_endpoint: str
    - request_body: Dict or property that returns Dict (prepared request)
    - get_header_dict(): Dict (auth headers)

    Optional: override parse_* methods for custom parsing logic.
    """

    # Must be implemented by agent subclass
    NAME: str = ""
    api_endpoint: str = ""

    def get_header_dict(self) -> Dict[str, str]:
        """Must be implemented by agent subclass"""
        raise NotImplementedError("Subclass must implement get_header_dict()")

    # =========================================================================
    # Parsers (Case-Specific Extractors)
    # =========================================================================

    def parse_request(
        self,
        method: str = "POST",
        raw_response: Optional[Dict[str, Any]] = None,
        http_status: int = 0,
        execution_time_ms: int = 0,
        success: bool = True,
        error_message: Optional[str] = None,
        response_type: str = "real_call"
    ) -> Dict[str, Any]:
        """
        Extract RequestModel data from agent state.

        This parser captures the complete raw API request and response.
        Called AFTER the API request is made to include the response.

        Args:
            method: HTTP method (default: POST)
            raw_response: Raw API response dict
            http_status: HTTP status code from API
            execution_time_ms: Time taken for API call
            success: Whether API call succeeded
            error_message: Error message if failed
            response_type: "real_call" (fresh API) or "cached_response" (from cache)

        Returns:
            dict with RequestModel data_value:
            {
                'agent_name': str,
                'url': str,
                'method': str,
                'headers': Dict,
                'body': Dict,
                'raw_response': Optional[Dict],
                'http_status': int,
                'response_type': str,
                'execution_time_ms': int,
                'success': bool,
                'error_message': Optional[str]
            }
        """
        return {
            'agent_name': self.NAME,
            'url': self.api_endpoint,
            'method': method,
            'headers': self.get_header_dict(),
            'body': self.request_body.copy(),
            'raw_response': raw_response,
            'http_status': http_status,
            'response_type': response_type,
            'execution_time_ms': execution_time_ms,
            'success': success,
            'error_message': error_message
        }

    def parse_query(
        self,
        request_id: str,
        query_keywords: Optional[List[str]] = None,
        query_topics: Optional[List[str]] = None,
        days_back: Optional[int] = None,
        time_filter: Optional[str] = None,
        max_results: Optional[int] = None,
        language: Optional[str] = None,
        agent_specific_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract QueryModel data from agent state.

        This parser normalizes common query fields across different agent APIs.
        Agents can override to extract specific fields from their request_body.

        Args:
            request_id: Associated RequestModel ID (required)
            query_keywords: Main search keywords (default: extract from request_body)
            query_topics: Sub-topics or focus areas
            days_back: Number of days to search back
            time_filter: Time filter string (e.g., "oneWeek", "week")
            max_results: Maximum results requested
            language: Language code (e.g., "zh", "en")
            agent_specific_params: Raw agent-specific parameters

        Returns:
            dict with QueryModel data_value:
            {
                'agent_name': str,
                'query_keywords': List[str],
                'query_topics': List[str],
                'days_back': Optional[int],
                'time_filter': Optional[str],
                'max_results': Optional[int],
                'language': Optional[str],
                'agent_specific_params': Dict,
                'raw_query_body': Dict
            }
        """
        # Default: try to extract from request_body if not provided
        if query_keywords is None:
            query_keywords = self._extract_query_keywords()

        return {
            'agent_name': self.NAME,
            'query_keywords': query_keywords or [],
            'query_topics': query_topics or [],
            'days_back': days_back,
            'time_filter': time_filter,
            'max_results': max_results,
            'language': language,
            'agent_specific_params': agent_specific_params or {},
            'raw_query_body': self.request_body.copy()
        }

    def parse_response_items(
        self,
        raw_response: Dict[str, Any],
        item_parser: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract ResponseItem list from raw API response.

        This parser converts a raw API response into a list of normalized
        search result items. Must be implemented by subclass or provided
        via item_parser callback.

        Args:
            raw_response: Raw API response dict
            item_parser: Optional callable(item_dict) -> ResponseItem data_value
                        If not provided, calls self._parse_response_item()

        Returns:
            List of dicts, each with ResponseItem data_value:
            [{
                'agent_name': str,
                'title': str,
                'content': str,
                'source_url': str,
                'source_name': str,
                'category': Optional[str],
                'key_entities': List[str],
                'relevance_score': Optional[float],
                'significance': Optional[str],
                'agent_metadata': Dict
            }, ...]
        """
        items = []

        if not raw_response:
            return items

        # Extract items from response based on agent type
        response_items = self._extract_response_items(raw_response)

        for item_data in response_items:
            if item_parser:
                # Use custom parser if provided
                parsed = item_parser(item_data)
            else:
                # Use agent's default parser
                parsed = self._parse_response_item(item_data)

            if parsed:
                items.append(parsed)

        return items

    # =========================================================================
    # Internal Extraction Methods (override in subclasses for custom logic)
    # =========================================================================

    def _extract_query_keywords(self) -> List[str]:
        """
        Extract query keywords from request_body.

        Default implementation returns empty list.
        Override in agent subclass to extract from agent-specific fields.

        Example (BOCHA):
            if 'query' in self.request_body:
                return [self.request_body['query']]

        Example (XUNFEI):
            messages = self.request_body.get('messages', [])
            if messages and messages[0].get('content'):
                return [messages[0]['content'][:50]]  # First 50 chars
        """
        return []

    def _extract_response_items(self, raw_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract items list from raw API response.

        Default implementation returns empty list.
        Override in agent subclass to extract items from agent-specific response format.

        Example (BOCHA):
            return raw_response.get('webPages', [])

        Example (XUNFEI):
            return raw_response.get('choices', [])
        """
        return []

    def _parse_response_item(self, item_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse a single item from agent's response format to ResponseItem data_value.

        Default implementation returns None (no items parsed).
        Override in agent subclass with agent-specific parsing logic.

        Example (BOCHA):
            return {
                'title': item_data.get('name'),
                'content': item_data.get('snippet'),
                'source_url': item_data.get('url'),
                'source_name': 'BOCHA',
                'agent_metadata': item_data
            }

        Example (XUNFEI):
            content = item_data.get('message', {}).get('content', '')
            return {
                'title': content[:100],
                'content': content,
                'source_url': '',
                'source_name': 'XUNFEI',
                'agent_metadata': item_data
            }
        """
        return None
