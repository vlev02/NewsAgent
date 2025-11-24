"""Xunfei Spark AI Search API agent implementation with Jinja2 template support"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Literal

from pydantic import Field

from .config import AgentConfig
from src.utils import get_api_time_filter, get_time_description, load_jinja_template
from src.debug_config import DebugConfig
from .base import SearchAgent
from .request_schema import RequestSchema, TemplateSchema


class XunfeiTemplateSchema(TemplateSchema):
    """
    Xunfei Spark template variables schema.

    Defines all template variables used for Jinja2 prompt rendering.
    All defaults come from config/agents.yaml (XUNFEI template_vars section).

    Template variables:
    - query_fields: List of technology domains to search
    - query_topics: List of specific topics to focus on
    - current_date: Current date in YYYY-MM-DD format
    - language: Language for search (default: 中文)
    """

    query_fields: List[str] = Field(
        default_factory=list,
        description="Technology domains to search for (e.g., 自动驾驶, 人工智能)"
    )

    query_topics: List[str] = Field(
        default_factory=list,
        description="Specific topics to focus on (e.g., 特斯拉FSD, AI大模型突破)"
    )

    current_date: str = Field(
        default_factory=lambda: __import__('datetime').datetime.now().strftime("%Y-%m-%d"),
        description="Current date in YYYY-MM-DD format for template rendering"
    )

    language: str = Field(
        default="中文",
        description="Search language"
    )


class XunfeiRequestSchema(RequestSchema):
    """
    Xunfei Spark AI Search API request body schema.

    Xunfei uses a message-based LLM interface with AI-powered search capabilities.
    The request includes messages, model configuration, and web search tools.

    Key differences from other LLM agents:
    - Uses 'messages' array with role/content structure
    - Messages auto-generated from template rendering
    - Includes 'user' field for user identification
    - Has 'tools' array with structured web_search configuration
    - Temperature is float (not string like Qianfan)
    - Uses 'max_tokens' instead of 'max_completion_tokens'
    """

    # Message configuration (for LLM/Chat interface)
    messages: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="Message history for chat-based search (auto-generated from template)"
    )

    # Model configuration
    model: str = Field(
        default="4.0Ultra",
        description="Model to use (4.0Ultra, 4.0, 3.5, etc.)"
    )

    # User identification
    user: str = Field(
        default="tech_news_agent",
        description="User identifier for the request"
    )

    # Generation parameters
    stream: bool = Field(
        default=False,
        description="Whether to stream the response"
    )

    temperature: float = Field(
        default=0.3,
        description="Temperature for output diversity (lower = more deterministic)"
    )

    max_tokens: int = Field(
        default=4000,
        description="Maximum tokens for generation"
    )

    # Tools configuration for web search
    tools: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Tools array with web_search configuration"
    )


class XunfeiAgent(SearchAgent):
    """
    Agent for Xunfei Spark AI Search API.

    Xunfei provides an LLM-based search interface with web search capabilities.
    It supports advanced reasoning and is optimized for Chinese language content analysis.

    Key Features:
    - Web search integration via tools array
    - Deep search mode for comprehensive results
    - Optimized for Chinese technical news analysis
    - Jinja2 template-based prompt generation
    - User identification for request tracking

    Template System:
    - Template path configured in agents.yaml (template.path)
    - Template variables from agents.yaml (template_vars)
    - Dynamic prompt generation based on variables
    - Auto-generates 'messages' array from rendered template
    - Search configuration in query_body

    Configuration Structure (agents.yaml):
    ```yaml
    XUNFEI:
      type: "LLM_SEARCH"
      endpoint: "https://spark-api-open.xf-yun.com/v1/chat/completions"
      auth_header: "Authorization"

      # Template configuration (separate from query_body)
      template:
        path: "src/templates/xunfei_prompt.jinja2"
        name: "xunfei_prompt"

      # Template variables for Jinja2 rendering
      template_vars:
        query_fields: [...]
        query_topics: [...]
        current_date: "2025-11-21"
        language: "中文"

      # API request body configuration
      query_body:
        model: "4.0Ultra"
        user: "tech_news_agent"
        stream: false
        temperature: 0.3
        max_tokens: 4000
    ```

    API Keys Required:
    - XUNFEI_API_KEY: The API key for Xunfei Spark service
    """

    NAME: str = "XUNFEI"
    api_keys: List[str] = ["XUNFEI_API_KEY"]

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
        If not configured, uses default: src/templates/xunfei_prompt.jinja2
        """
        try:
            # Get template path from configuration
            template_config = config.template_config
            template_path = template_config.get('path')

            if not template_path:
                # Use default path
                default_path = Path(__file__).parent.parent / "templates" / "xunfei_prompt.jinja2"
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
            print(f"Warning: Failed to load Xunfei template: {e}")
            return None

    def _initialize_template_schema(self):
        """Create and return initialized TemplateSchema instance.

        The schema is created with variables from template_vars.
        """
        # Get the fields defined in the schema
        schema_fields = XunfeiTemplateSchema.model_fields.keys()

        # Filter template_vars to only include schema-defined fields
        filtered_vars = {
            key: value
            for key, value in self._template_vars.items()
            if key in schema_fields
        }

        # Create instance with filtered template_vars as defaults
        return XunfeiTemplateSchema(**filtered_vars)

    def get_header_dict(self) -> Dict[str, str]:
        """
        Get HTTP headers for Xunfei API requests.

        Uses Authorization header with Bearer token.

        Returns:
            Dict with Authorization header and content type
        """
        api_key = self.api_keys_dict.get("XUNFEI_API_KEY", "")
        headers = {
            self.auth_header_name: f"{self.auth_prefix} {api_key}",
            "Content-Type": "application/json"
        }
        return headers

    def _get_request_schema_class(self) -> Type:
        """
        Get the RequestSchema class for XUNFEI.

        Returns:
            XunfeiRequestSchema class
        """
        return XunfeiRequestSchema

    def _render_prompt_template(self) -> str:
        """
        Render the Jinja2 template for the search prompt.

        Uses current template variables from template_schema.

        Returns:
            Rendered prompt string
        """
        if not self._template:
            # Fallback to simple prompt if template not available
            return "请获取最近一周的技术资讯"

        try:
            # Get all template variables from schema
            template_vars = self.template_schema.validate_and_get_dict()
            return self._template.render(**template_vars)
        except Exception as e:
            print(f"Warning: Template rendering failed: {e}")
            return "请获取最近一周的技术资讯"

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
        3. Build tools array for web search if not explicitly set
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

        # Build tools array for web search if not explicitly set
        if not body.get("tools"):
            # Get search configuration from request body args
            search_mode = self._request_body_args.get("search_mode", "deep")

            # Build web_search tools configuration
            body["tools"] = [
                {
                    "type": "web_search",
                    "web_search": {
                        "enable": True,
                        "search_mode": search_mode
                    }
                }
            ]

        return body
