"""Abstract base class for all search agents"""

import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Type, Union
from uuid import uuid4

from src.dataclasses import AgentConfig, QueryRequest, QueryResponse, SearchItem
from src.utils.simu_request import SimuRequest
from src.data_manager import AgentDataWrapper
import requests

class SearchAgent(ABC, AgentDataWrapper):
    """
    Abstract base class for all search agents.

    Each agent must implement methods for:
    - Building API-specific queries
    - Submitting requests
    - Parsing responses
    - Normalizing timestamps
    - Managing RequestSchema for request validation

    Configuration Pattern:
    - Agent receives AgentConfig with query_body defaults from agents.yaml
    - Agent creates and maintains a RequestSchema instance during __init__
    - RequestSchema validates and provides default values for requests
    - Any modification to query_body should update the RequestSchema

    API Key Management:
    - Each agent declares required api_keys (class attribute)
    - Example: api_keys = ["BOCHA_API_KEY"] or ["XUNFEI_APPID", "XUNFEI_APIKey"]
    - AgentManager acquires keys from its all_keys dict or environment variables
    - Keys are injected into agent config during initialization
    """

    # Class-level NAME property - fixed identifier for this agent
    NAME: str = None  # Must be overridden in subclasses

    # Class-level api_keys - list of required API keys for this agent
    api_keys: List[str] = []  # Override in subclasses if agent needs specific keys

    def __init__(self, config: AgentConfig):
        """
        Initialize search agent.

        Args:
            config: AgentConfig specifying agent parameters, query_body defaults, and template config
        """
        # Extract config values into separate attributes
        self.agent_type = config.agent_type
        self.api_endpoint = config.api_endpoint
        self.auth_header_name = config.auth_header_name
        self.auth_prefix = config.auth_prefix
        self.api_keys_dict = config.api_keys

        # Extract query_body defaults from config
        self._request_body_args = {}
        self.request_body_args = config.request_body_params.copy()

        # Extract template configuration (for LLM_SEARCH agents)
        self._template_config = config.template_config.copy()
        self._template_vars = {}
        self.template_vars = config.template_vars.copy()

    @property
    def request_body(self) -> Dict[str, Any]:
        """
        Get current request body ready for requests.post (read-only).

        This is dynamically generated from request_schema and returns the
        validated request body that will be sent in the HTTP request.
        To update, use the request_body_args property setter.

        Returns:
            Dict with validated request body parameters ready for API call
        """
        return self.request_schema.validate_and_get_dict()

    @property
    def request_body_args(self) -> Dict[str, Any]:
        """
        Get current request body arguments.

        Returns:
            Dict with all request body parameters
        """
        return self._request_body_args.copy()

    @request_body_args.setter
    def request_body_args(self, value: Dict[str, Any]) -> None:
        """
        Update request body arguments and refresh RequestSchema.

        Updates _request_body_args and reinitializes the RequestSchema.
        The request_body property will automatically reflect changes.

        Args:
            value: New request body args dict
        """
        self._request_body_args.update(value)
        # Update the request schema with new defaults
        self.request_schema = self._initialize_request_schema()

    @property
    def template_vars(self) -> Dict[str, Any]:
        """
        Get current template variables.

        Returns:
            Dict with all template variables
        """
        return self._template_vars.copy()

    @template_vars.setter
    def template_vars(self, value: Dict[str, Any]) -> None:
        """
        Update template variables.

        Updates _template_vars with new variables.
        Subclasses can override to implement template re-rendering.

        Args:
            value: New template variables dict
        """
        self._template_vars.update(value)

    @property
    def template_config(self) -> Dict[str, Any]:
        """
        Get template configuration (path, name, etc).

        Returns:
            Dict with template configuration
        """
        return self._template_config.copy()

    @abstractmethod
    def _get_request_schema_class(self) -> Type:
        """
        Get the RequestSchema class for this agent.

        Returns:
            The Pydantic RequestSchema class (e.g., BochaRequestSchema)
        """
        pass

    def _initialize_request_schema(self):
        """
        Create and return initialized RequestSchema instance.

        The schema is created with defaults from request_body_args.
        Only passes fields that are defined in the schema (filters out config-only params).
        Override in subclasses if custom initialization is needed.

        Returns:
            Initialized RequestSchema instance
        """
        schema_class = self._get_request_schema_class()

        # Get the fields defined in the schema
        schema_fields = schema_class.model_fields.keys()

        # Filter request_body_args to only include schema-defined fields
        filtered_args = {
            key: value
            for key, value in self._request_body_args.items()
            if key in schema_fields
        }

        # Create instance with filtered request_body_args as defaults
        return schema_class(**filtered_args)
    
    @abstractmethod
    def get_header_dict(self) -> Dict[str, str]:
        """
        Get HTTP headers for API requests.

        Extracts API keys from api_keys_dict and constructs headers.

        Returns:
            Dict with Authorization header and any other required headers
        """
        pass

    @SimuRequest.simu_request
    def submit_request(self):
        """
        Submit request to API with optional caching via SimuRequest decorator.

        The SimuRequest decorator automatically:
        - Caches responses based on class name and method name
        - Handles cache hits/misses based on simu_call and update_response flags
        - Logs cache operations based on log_calls flag

        Configuration is controlled by:
        - config/simu_call.yaml (default settings)
        - SimuRequest.update_behaviors() (runtime changes)

        Returns:
            Dict with API response or cached response
        """
        # Prepare HTTP request arguments
        request_args = {
            "url": self.api_endpoint,
            "method": "POST",
            "json": self.request_body,  # Only API-relevant fields
            "headers": self.get_header_dict(),  # Authorization header
            "timeout": 120,
            "proxies": {},  # Disable proxy for direct API connection
        }

        # Store request metadata for decorator to capture
        self._last_request_metadata = request_args.copy()

        api_response = requests.request(**request_args)
        try:
            response_json = api_response.json()
        except:
            response_json = {
                "code": "unknown",
                "content": str(api_response)
            }
        return response_json