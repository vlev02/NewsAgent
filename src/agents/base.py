"""Abstract base class for all search agents"""

import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from jinja2 import Template

from src.dataclasses import AgentConfig, QueryRequest, QueryResponse, SearchItem


class SearchAgent(ABC):
    """
    Abstract base class for all search agents.

    Each agent must implement methods for:
    - Building API-specific queries
    - Submitting requests
    - Parsing responses
    - Normalizing timestamps

    Template rendering and budget tracking are provided by the base class.
    """

    def __init__(self, config: AgentConfig):
        """
        Initialize search agent.

        Args:
            config: AgentConfig specifying agent parameters
        """
        self.config = config
        self.prompt_template: Optional[Template] = None
        self._initialize_budget_tracking()

        # Load prompt template if applicable
        if self.config.agent_type == "LLM_SEARCH":
            self.prompt_template = self._load_prompt_template()

    @abstractmethod
    def _initialize_budget_tracking(self) -> None:
        """
        Initialize budget and quota tracking.

        Subclasses should track:
        - Daily quota usage
        - Monthly budget consumption
        - Rate limit state
        """
        pass

    @abstractmethod
    def _load_prompt_template(self) -> Optional[Template]:
        """
        Load and return Jinja2 template for this agent.

        Returns:
            Jinja2 Template or None if not applicable
        """
        pass

    @abstractmethod
    def build_query(self, request: QueryRequest) -> Union[str, Dict[str, Any]]:
        """
        Build API-specific query from QueryRequest.

        Args:
            request: QueryRequest with search parameters

        Returns:
            String (for REST APIs) or Dict (for LLM APIs)
        """
        pass

    def render_prompt(self,
                     query_fields: List[str],
                     query_topics: List[str],
                     **kwargs) -> str:
        """
        Render Jinja2 prompt template with provided parameters.

        Automatically injects common parameters like date and language.

        Args:
            query_fields: Main search domains
            query_topics: Specific topics to focus on
            **kwargs: Additional template parameters

        Returns:
            Rendered prompt string
        """
        if not self.prompt_template:
            raise ValueError(f"Agent {self.config.agent_name} does not have a prompt template")

        context = {
            "query_fields": query_fields,
            "query_topics": query_topics,
            "current_date": datetime.now().strftime("%Y-%m-%d"),
            "current_datetime": datetime.now().isoformat(),
            "agent_name": self.config.agent_name,
            "language": self.config.default_params.get("language", "zh"),
            **kwargs
        }
        return self.prompt_template.render(context)

    def check_budget(self) -> bool:
        """
        Check if agent has remaining budget/quota.

        Returns:
            True if budget available, False if exceeded
        """
        pass

    def check_rate_limit(self) -> bool:
        """
        Check if within rate limit.

        Returns:
            True if can make request, False if should wait
        """
        pass

    def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status.

        Returns:
            Dict with fields:
            - agent_name: str
            - is_available: bool
            - budget_remaining: float
            - quota_remaining: int
            - last_call_time: datetime
            - calls_today: int
        """
        pass

    @abstractmethod
    def submit_request(self,
                      query: Union[str, Dict[str, Any]],
                      request: QueryRequest) -> QueryResponse:
        """
        Execute the actual API call.

        Handles authentication, request building, and response parsing.

        Args:
            query: Prepared query (string or dict)
            request: Original QueryRequest for context

        Returns:
            QueryResponse with results
        """
        pass

    @abstractmethod
    def parse_response(self, raw_response: Any) -> List[SearchItem]:
        """
        Parse raw API response into normalized SearchItem list.

        Handles API-specific response structures and formats.

        Args:
            raw_response: Raw API response

        Returns:
            List of SearchItem objects
        """
        pass

    @abstractmethod
    def normalize_timestamp(self, timestamp_str: str) -> datetime:
        """
        Convert API-specific timestamp format to datetime.

        Args:
            timestamp_str: Timestamp in API-specific format

        Returns:
            Normalized datetime object
        """
        pass

    def submit_and_parse(self, request: QueryRequest) -> QueryResponse:
        """
        High-level method: build query, submit, parse, return QueryResponse.

        Includes error handling, budget checking, and metrics collection.

        Args:
            request: QueryRequest to execute

        Returns:
            QueryResponse with all data
        """
        try:
            # Build query
            query = self.build_query(request)

            # Check limits
            if not self.check_budget():
                return QueryResponse(
                    response_id=str(uuid4()),
                    agent_name=self.config.agent_name,
                    query_id=request.query_id,
                    timestamp=datetime.now(),
                    items=[],
                    success=False,
                    status="quota_exceeded",
                    error_message="Budget exceeded"
                )

            if not self.check_rate_limit():
                return QueryResponse(
                    response_id=str(uuid4()),
                    agent_name=self.config.agent_name,
                    query_id=request.query_id,
                    timestamp=datetime.now(),
                    items=[],
                    success=False,
                    status="rate_limited",
                    error_message="Rate limit exceeded"
                )

            # Execute
            start_time = time.time()
            response = self.submit_request(query, request)
            response.execution_time_ms = int((time.time() - start_time) * 1000)
            response.response_id = str(uuid4())
            response.agent_name = self.config.agent_name
            response.query_id = request.query_id
            response.timestamp = datetime.now()

            return response

        except Exception as e:
            return QueryResponse(
                response_id=str(uuid4()),
                agent_name=self.config.agent_name,
                query_id=request.query_id,
                timestamp=datetime.now(),
                items=[],
                success=False,
                error_message=f"{type(e).__name__}: {str(e)}",
                status="failed"
            )

    def get_header_dict(self) -> Dict[str, str]:
        """
        Get HTTP headers for API requests.

        Returns:
            Dict with Authorization header and others
        """
        headers = {
            self.config.auth_header_name: f"{self.config.auth_prefix} {self.config.api_key}",
            "Content-Type": "application/json"
        }
        return headers
