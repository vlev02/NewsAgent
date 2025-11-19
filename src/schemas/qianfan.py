"""Baidu Qianfan LLM API request schema"""

from typing import Literal, Optional
from pydantic import Field
from .base import RequestSchema


class QianfanRequestSchema(RequestSchema):
    """
    Baidu Qianfan LLM API request body schema.

    Qianfan API expects:
    - model: model version
    - query: search query
    - search_source: search source
    - enable_reasoning: enable reasoning
    - temperature: sampling temperature
    - top_p: nucleus sampling
    - max_completion_tokens: max tokens
    """

    model: Literal["deepseek-r1", "ernie-4.0", "ernie-3.5"] = Field(
        default="deepseek-r1",
        description="Qianfan model version"
    )

    query: str = Field(
        default="人工智能",
        min_length=1,
        max_length=2000,
        description="Search/question query"
    )

    search_source: Literal["baidu_search_v2", "baidu_search_v1"] = Field(
        default="baidu_search_v2",
        description="Search source"
    )

    enable_reasoning: bool = Field(
        default=True,
        description="Enable reasoning in response"
    )

    temperature: float = Field(
        default=1e-10,
        ge=0.0,
        le=1.0,
        description="Sampling temperature (0.0-1.0)"
    )

    top_p: float = Field(
        default=1e-10,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling parameter"
    )

    max_completion_tokens: int = Field(
        default=20480,
        ge=100,
        le=32000,
        description="Maximum completion tokens"
    )

    class Config:
        """Pydantic configuration"""
        extra = "allow"
        validate_assignment = True
