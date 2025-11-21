"""Baidu Qianfan AI Search API agent implementation with Jinja2 template support"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Literal

from pydantic import Field

from src.dataclasses import AgentConfig, QueryRequest, QueryResponse, SearchItem
from src.utils import get_api_time_filter, get_time_description, load_jinja_template
from src.decorators import handle_api_request
from src.debug_config import DebugConfig
from .base import SearchAgent
from .request_schema import RequestSchema, TemplateSchema


class QianfanTemplateSchema(TemplateSchema):
    """
    Baidu Qianfan template variables schema.

    Defines all template variables used for Jinja2 prompt rendering.
    All defaults come from config/agents.yaml (QIANFAN template_vars section).

    Template variables:
    - query_fields: List of technology domains to search
    - query_topics: List of specific topics to focus on
    - time_description: Human-readable time range (e.g., "最近一周")
    - resource_types: List of resource types (web, image, video)
    - language: Language for search (default: 中文)
    - enable_reasoning: Whether to enable reasoning analysis
    """

    query_fields: List[str] = Field(
        default_factory=list,
        description="Technology domains to search for (e.g., 自动驾驶, 人工智能)"
    )

    query_topics: List[str] = Field(
        default_factory=list,
        description="Specific topics to focus on (e.g., 特斯拉FSD, AI大模型突破)"
    )

    time_description: str = Field(
        default="最近一周",
        description="Human-readable time range for search"
    )

    resource_types: List[str] = Field(
        default_factory=lambda: ["网页", "图片", "视频"],
        description="Types of resources to search (web, image, video)"
    )

    language: str = Field(
        default="中文",
        description="Search language"
    )

    enable_reasoning: bool = Field(
        default=True,
        description="Whether to enable reasoning analysis in output"
    )


class QianfanRequestSchema(RequestSchema):
    """
    Baidu Qianfan AI Search API request body schema.

    Qianfan uses a message-based LLM interface with AI-powered search capabilities.
    The request includes messages, model configuration, search settings, and resource filters.

    Key differences from REST API agents:
    - Uses 'messages' array with role/content structure
    - Messages auto-generated from template rendering
    - Includes search source configuration and resource type filtering
    - Supports reasoning mode for DeepSeek models
    """

    # Message configuration (for LLM/Chat interface)
    messages: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="Message history for chat-based search (auto-generated from template)"
    )

    # Model configuration
    model: str = Field(
        default="deepseek-r1",
        description="Model to use (deepseek-r1, ernie-3.5-8k, ernie-4.5-turbo-32k, etc.)"
    )

    stream: bool = Field(
        default=False,
        description="Whether to stream the response"
    )

    temperature: str = Field(
        default="1e-10",
        description="Temperature for deterministic output (1e-10 for consistent results)"
    )

    top_p: str = Field(
        default="1e-10",
        description="Top-p sampling parameter (1e-10 for consistent results)"
    )

    # Search configuration
    search_source: str = Field(
        default="baidu_search_v2",
        description="Search source (baidu_search_v2 recommended for better performance)"
    )

    search_mode: Literal["required", "optional"] = Field(
        default="required",
        description="Whether search is required or optional"
    )

    search_recency_filter: Literal["week", "month", "semiyear", "year"] = Field(
        default="week",
        description="Time filter for search results"
    )

    # Resource type filtering
    resource_type_filter: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Filter resource types (web, image, video) with top_k limits"
    )

    # Search behavior
    enable_deep_search: bool = Field(
        default=False,
        description="Enable deep search (more thorough, uses more calls)"
    )

    enable_corner_markers: bool = Field(
        default=True,
        description="Enable corner markers for reference attribution"
    )

    enable_followup_queries: bool = Field(
        default=False,
        description="Enable follow-up queries"
    )

    max_search_query_num: int = Field(
        default=10,
        description="Maximum number of search queries to generate"
    )

    max_completion_tokens: str = Field(
        default="20480",
        description="Maximum tokens for generation"
    )

    # Model-specific features
    enable_reasoning: bool = Field(
        default=True,
        description="Enable reasoning mode (for deepseek-r1 model)"
    )


class QianfanAgent(SearchAgent):
    """
    Agent for Baidu Qianfan AI Search API.

    Qianfan provides an LLM-based search interface with AI-powered analysis and reasoning.
    Supports multiple models (deepseek-r1, ernie series) with optional reasoning chains.

    Key Features:
    - Real-time internet search with Baidu search engine
    - AI-powered summarization and analysis
    - Multi-type resource filtering (web, image, video)
    - Reasoning mode for DeepSeek models
    - Jinja2 template-based prompt generation
    - Time-based filtering for recent information

    Template System:
    - Template path configured in agents.yaml (template.path)
    - Template variables from agents.yaml (template_vars)
    - Dynamic prompt generation based on variables
    - Auto-generates 'messages' array from rendered template
    - Resource types and reasoning configured in query_body

    Configuration Structure (agents.yaml):
    ```yaml
    QIANFAN:
      type: "LLM_SEARCH"
      endpoint: "https://qianfan.baidubce.com/v2/ai_search/chat/completions"
      auth_header: "X-Appbuilder-Authorization"

      # Template configuration (separate from query_body)
      template:
        path: "src/templates/qianfan_prompt.jinja2"
        name: "qianfan_prompt.jinja2"

      # Template variables for Jinja2 rendering
      template_vars:
        query_fields: [...]
        query_topics: [...]
        time_description: "最近一周"
        resource_types: [...]
        language: "中文"
        enable_reasoning: true

      # API request body configuration
      query_body:
        model: "deepseek-r1"
        stream: false
        temperature: "1e-10"
        search_source: "baidu_search_v2"
        search_mode: "required"
        search_recency_filter: "week"
        resource_config:
          image: 4
          video: 4
          web: 4
        enable_deep_search: false
        enable_corner_markers: true
        enable_followup_queries: false
        max_search_query_num: 10
        max_completion_tokens: "20480"
        enable_reasoning: true
    ```

    API Keys Required:
    - QIANFAN_API_KEY: The API key for Qianfan service (AppBuilder API Key)
    """

    NAME: str = "QIANFAN"
    api_keys: List[str] = ["QIANFAN_API_KEY"]

    def __init__(self, config: AgentConfig):
        # Load Jinja2 template BEFORE calling super().__init__
        # because super().__init__ will trigger template rendering
        self._template = self._load_template(config)
        super().__init__(config)
        # Initialize template schema for variable validation
        self.template_schema = self._initialize_template_schema()

    def _load_template(self, config: AgentConfig):
        """Load the Jinja2 template based on config.

        Template path is read from config.template_config['path'].
        If not configured, uses default: src/templates/qianfan_prompt.jinja2
        """
        try:
            # Get template path from configuration
            template_config = config.template_config
            template_path = template_config.get('path')

            if not template_path:
                # Use default path
                default_path = Path(__file__).parent.parent / "templates" / "qianfan_prompt.jinja2"
                template_path = str(default_path)
            else:
                # Convert relative path to absolute if needed
                path = Path(template_path)
                if not path.is_absolute():
                    # Relative to project root
                    project_root = Path(__file__).parent.parent.parent
                    path = project_root / path
                template_path = str(path)

            return load_jinja_template(template_path)
        except Exception as e:
            print(f"Warning: Failed to load Qianfan template: {e}")
            return None

    def _initialize_template_schema(self):
        """Create and return initialized TemplateSchema instance.

        The schema is created with variables from template_vars.
        """
        # Get the fields defined in the schema
        schema_fields = QianfanTemplateSchema.model_fields.keys()

        # Filter template_vars to only include schema-defined fields
        filtered_vars = {
            key: value
            for key, value in self._template_vars.items()
            if key in schema_fields
        }

        # Create instance with filtered template_vars as defaults
        return QianfanTemplateSchema(**filtered_vars)

    def get_header_dict(self) -> Dict[str, str]:
        """
        Get HTTP headers for Qianfan API requests.

        Uses X-Appbuilder-Authorization header with Bearer token.

        Returns:
            Dict with Authorization header and content type
        """
        api_key = self.api_keys_dict.get("QIANFAN_API_KEY", "")
        headers = {
            "X-Appbuilder-Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        return headers

    def _get_request_schema_class(self) -> Type:
        """
        Get the RequestSchema class for QIANFAN.

        Returns:
            QianfanRequestSchema class
        """
        return QianfanRequestSchema

    def _render_prompt_template(self) -> str:
        """
        Render the Jinja2 template for the search prompt.

        Uses current template variables from template_schema.

        Returns:
            Rendered prompt string
        """
        if not self._template:
            # Fallback to simple prompt if template not available
            return "请搜索最近一周的相关内容"

        try:
            # Get all template variables from schema
            template_vars = self.template_schema.validate_and_get_dict()
            return self._template.render(**template_vars)
        except Exception as e:
            print(f"Warning: Template rendering failed: {e}")
            return "请搜索最近一周的相关内容"

    @property
    def template_vars(self) -> Dict[str, Any]:
        """
        Get current template variables (overrides base class).

        Returns:
            Dict with all template variables
        """
        return self.template_schema.validate_and_get_dict()

    @template_vars.setter
    def template_vars(self, value: Dict[str, Any]) -> None:
        """
        Update template variables and re-render template (overrides base class).

        Updates the template schema with new variables.
        Messages array will be automatically regenerated on next request_body access.

        Args:
            value: New template variables dict
        """
        self._template_vars.update(value)
        # Reinitialize template schema with new variables
        self.template_schema = self._initialize_template_schema()

    @property
    def request_body(self) -> Dict[str, Any]:
        """
        Get current request body ready for requests.post (read-only).

        Overrides base implementation to:
        1. Get validated body from schema
        2. If messages not set, auto-generate from template
        3. Build resource_type_filter if resource_config provided
        4. Ensure all required fields are present

        Returns:
            Dict with validated request body parameters ready for API call
        """
        body = self.request_schema.validate_and_get_dict()

        # Auto-generate messages from template if not explicitly set
        if not body.get("messages"):
            # Render template
            user_content = self._render_prompt_template()

            # Create messages array
            body["messages"] = [
                {
                    "role": "user",
                    "content": user_content
                }
            ]

        # Build resource_type_filter from resource_config if provided
        if "resource_config" in self._request_body_args and not body.get("resource_type_filter"):
            resource_config = self._request_body_args["resource_config"]
            if isinstance(resource_config, dict):
                body["resource_type_filter"] = [
                    {"type": res_type, "top_k": top_k}
                    for res_type, top_k in resource_config.items()
                ]

        return body
