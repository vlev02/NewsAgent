"""Tencent Hunyuan LLM API request schema"""

from typing import Literal, Optional
from pydantic import Field
from .base import RequestSchema


class HunyuanRequestSchema(RequestSchema):
    """
    Tencent Hunyuan LLM API request body schema.

    Hunyuan API expects:
    - model: model version
    - query: search query
    - temperature: sampling temperature
    - enable_enhancement: enable response enhancement
    - search_info: include search information
    """

    model: Literal["hunyuan-turbo", "hunyuan-pro", "hunyuan-standard"] = Field(
        default="hunyuan-turbo",
        description="Hunyuan model version"
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

    enable_enhancement: bool = Field(
        default=True,
        description="Enable response enhancement"
    )

    search_info: bool = Field(
        default=True,
        description="Include search information in response"
    )

    class Config:
        """Pydantic configuration"""
        extra = "allow"
        validate_assignment = True
