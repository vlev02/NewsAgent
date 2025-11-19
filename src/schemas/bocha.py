"""BOCHA Web Search API request schema"""

from typing import Literal, Optional
from pydantic import Field
from .base import RequestSchema


class BochaRequestSchema(RequestSchema):
    """
    BOCHA Web Search API request body schema.

    BOCHA API expects:
    - query: single keyword string
    - freshness: time filter enum
    - count: number of results (1-100)
    - summary: boolean for AI summary
    """

    query: str = Field(
        default="人工智能",
        min_length=1,
        max_length=1000,
        description="Search query keywords (1-1000 characters)"
    )

    freshness: Literal["oneDay", "oneWeek", "oneMonth", "oneYear"] = Field(
        default="oneWeek",
        description="Time filter for search results (oneDay, oneWeek, oneMonth, oneYear)"
    )

    count: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of results to return (1-100)"
    )

    summary: bool = Field(
        default=True,
        description="Include AI-generated summary in results"
    )

    class Config:
        """Pydantic configuration"""
        extra = "allow"  # Allow additional BOCHA-specific parameters
        validate_assignment = True
