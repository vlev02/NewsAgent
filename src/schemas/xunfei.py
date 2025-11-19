"""Xunfei Spark LLM API request schema"""

from typing import Literal, Optional
from pydantic import Field
from .base import RequestSchema


class XunfeiRequestSchema(RequestSchema):
    """
    Xunfei Spark LLM API request body schema.

    Xunfei API expects:
    - model: model version
    - query: search query
    - temperature: sampling temperature
    - max_tokens: max completion tokens
    - search_mode: search depth
    """

    model: Literal["4.0Ultra", "4.0", "3.5"] = Field(
        default="4.0Ultra",
        description="Xunfei model version"
    )

    query: str = Field(
        default="人工智能",
        min_length=1,
        max_length=2000,
        description="Search/question query"
    )

    temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Sampling temperature (0.0-1.0)"
    )

    max_tokens: int = Field(
        default=4000,
        ge=100,
        le=8000,
        description="Maximum completion tokens"
    )

    search_mode: Literal["deep", "web", "document"] = Field(
        default="deep",
        description="Search mode/depth"
    )

    class Config:
        """Pydantic configuration"""
        extra = "allow"
        validate_assignment = True
