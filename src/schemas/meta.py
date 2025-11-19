"""META Search API request schema"""

from typing import Literal, Optional
from pydantic import Field
from .base import RequestSchema


class MetaRequestSchema(RequestSchema):
    """
    META Search API (https://metaso.cn/api/v1/search) request body schema.

    META API expects:
    - q: search query (supports time filters like "keyword 最近1天")
    - scope: search scope enum (webpage, blog, scholar, etc.)
    - size: number of results (as string)
    - includeSummary: boolean for AI summary inclusion
    - includeRawContent: boolean for raw content inclusion
    - conciseSnippet: boolean for concise snippet format
    """

    q: str = Field(
        default="人工智能",
        min_length=1,
        max_length=1000,
        description="Search query keywords. Supports time filters (e.g., '自动驾驶 最近1天' for last 1 day)"
    )

    scope: Literal["webpage", "blog", "scholar", "news", "academic", "patent", "arxiv"] = Field(
        default="webpage",
        description="Search scope/category (webpage, blog, scholar, news, academic, patent, arxiv)"
    )

    size: str = Field(
        default="10",
        description="Number of results to return as string (e.g., '3', '10')"
    )

    includeSummary: bool = Field(
        default=True,
        description="Include AI-generated summary in results"
    )

    includeRawContent: bool = Field(
        default=True,
        description="Include raw HTML/content in results"
    )

    conciseSnippet: bool = Field(
        default=True,
        description="Return concise snippet format"
    )

    class Config:
        """Pydantic configuration"""
        extra = "allow"  # Allow additional META-specific parameters
        validate_assignment = True
