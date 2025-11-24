"""Tencent Hunyuan AI Search API agent implementation with Jinja2 template support"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
from datetime import datetime

from pydantic import Field

from .config import AgentConfig
from src.utils import get_api_time_filter, get_time_description, load_jinja_template
from src.debug_config import DebugConfig
from .base import SearchAgent
from .request_schema import RequestSchema, TemplateSchema


class HunyuanTemplateSchema(TemplateSchema):
    """
    Tencent Hunyuan template variables schema.

    Defines all template variables used for Jinja2 prompt rendering.
    All defaults come from config/agents.yaml (HUNYUAN template_vars section).

    Template variables:
    - query_fields: List of technology domains to search
    - query_topics: List of specific topics to focus on
    - time_description: Human-readable time range (e.g., "最近一周")
    - current_date: Current date in YYYY-MM-DD format
    - language: Language for search (default: 中文)
    - enable_categorization: Whether to enable AI categorization
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

    current_date: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d"),
        description="Current date in YYYY-MM-DD format for template rendering"
    )

    language: str = Field(
        default="中文",
        description="Search language"
    )

    enable_categorization: bool = Field(
        default=True,
        description="Whether to enable automatic categorization of results"
    )


class HunyuanRequestSchema(RequestSchema):
    """
    Tencent Hunyuan AI Search API request body schema.

    Hunyuan uses a message-based LLM interface with AI-powered search capabilities.
    The request includes messages, model configuration, and search settings.

    Key differences from other LLM agents:
    - Uses 'messages' array with role/content structure
    - Messages auto-generated from template rendering
    - Supports Tencent-specific features like enable_enhancement and search_info
    - Optimized for Chinese language and tech news analysis
    """

    # Message configuration (for LLM/Chat interface)
    messages: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="Message history for chat-based search (auto-generated from template)"
    )

    # Model configuration
    model: str = Field(
        default="hunyuan-turbo",
        description="Model to use (hunyuan-turbo, hunyuan-pro, etc.)"
    )

    stream: bool = Field(
        default=False,
        description="Whether to stream the response"
    )

    temperature: float = Field(
        default=0.3,
        description="Temperature for output diversity (lower = more deterministic)"
    )

    # Hunyuan-specific features
    enable_enhancement: bool = Field(
        default=True,
        description="Enable Hunyuan's built-in enhancement features"
    )

    search_info: bool = Field(
        default=True,
        description="Enable real-time web search capability"
    )

    top_p: Optional[float] = Field(
        default=None,
        description="Top-p sampling parameter (optional)"
    )

    max_tokens: Optional[int] = Field(
        default=None,
        description="Maximum tokens for generation (optional)"
    )


class HunyuanAgent(SearchAgent):
    """
    Agent for Tencent Hunyuan AI Search API.

    Hunyuan provides an LLM-based search interface optimized for Chinese language
    and technical content analysis with automatic categorization and JSON-formatted responses.

    Key Features:
    - Real-time web search integration (search_info=true)
    - Enhanced output quality (enable_enhancement=true)
    - Automatic categorization of results
    - JSON-formatted response parsing
    - Optimized for Chinese technical news analysis
    - Jinja2 template-based prompt generation

    Template System:
    - Template path configured in agents.yaml (template.path)
    - Template variables from agents.yaml (template_vars)
    - Dynamic prompt generation based on variables
    - Auto-generates 'messages' array from rendered template
    - Search configuration in query_body

    Configuration Structure (agents.yaml):
    ```yaml
    HUNYUAN:
      type: "LLM_SEARCH"
      endpoint: "https://api.hunyuan.cloud.tencent.com/v1/chat/completions"
      auth_header: "Authorization"

      # Template configuration (separate from query_body)
      template:
        path: "src/templates/hunyuan_prompt.jinja2"
        name: "hunyuan_prompt"

      # Template variables for Jinja2 rendering
      template_vars:
        query_fields: [...]
        query_topics: [...]
        time_description: "最近一周"
        current_date: "2025-11-21"
        language: "中文"
        enable_categorization: true

      # API request body configuration
      query_body:
        model: "hunyuan-turbo"
        stream: false
        temperature: 0.3
        enable_enhancement: true
        search_info: true
    ```

    API Keys Required:
    - HUNYUAN_API_KEY: The API key for Hunyuan service
    """

    NAME: str = "HUNYUAN"
    api_keys: List[str] = ["HUNYUAN_API_KEY"]

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
        If not configured, uses default: src/templates/hunyuan_prompt.jinja2
        """
        try:
            # Get template path from configuration
            template_config = config.template_config
            template_path = template_config.get('path')

            if not template_path:
                # Use default path
                default_path = Path(__file__).parent.parent / "templates" / "hunyuan_prompt.jinja2"
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
            print(f"Warning: Failed to load Hunyuan template: {e}")
            return None

    def _initialize_template_schema(self):
        """Create and return initialized TemplateSchema instance.

        The schema is created with variables from template_vars.
        """
        # Get the fields defined in the schema
        schema_fields = HunyuanTemplateSchema.model_fields.keys()

        # Filter template_vars to only include schema-defined fields
        filtered_vars = {
            key: value
            for key, value in self._template_vars.items()
            if key in schema_fields
        }

        # Create instance with filtered template_vars as defaults
        return HunyuanTemplateSchema(**filtered_vars)

    def get_header_dict(self) -> Dict[str, str]:
        """
        Get HTTP headers for Hunyuan API requests.

        Uses Authorization header with Bearer token.

        Returns:
            Dict with Authorization header and content type
        """
        api_key = self.api_keys_dict.get("HUNYUAN_API_KEY", "")
        headers = {
            self.auth_header_name: f"{self.auth_prefix} {api_key}",
            "Content-Type": "application/json"
        }
        return headers

    def _get_request_schema_class(self) -> Type:
        """
        Get the RequestSchema class for HUNYUAN.

        Returns:
            HunyuanRequestSchema class
        """
        return HunyuanRequestSchema

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
        3. Ensure all required fields are present

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

        return body
