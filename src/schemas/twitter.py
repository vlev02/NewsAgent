"""Twitter/X API v2 request schema"""

from typing import Literal, Optional
from pydantic import Field
from .base import RequestSchema


class TwitterRequestSchema(RequestSchema):
    """
    Twitter/X API v2 request query schema.

    Twitter API expects:
    - query: search query string
    - sort_order: sorting order
    - max_results: number of results
    - start_time: search start time (ISO 8601)
    """

    query: str = Field(
        default="AI",
        min_length=1,
        max_length=512,
        description="Twitter search query"
    )

    sort_order: Literal["recency", "relevance", "engagement"] = Field(
        default="recency",
        description="Result sorting order"
    )

    max_results: int = Field(
        default=10,
        ge=10,
        le=100,
        description="Number of results to return (10-100)"
    )

    start_time: Optional[str] = Field(
        default=None,
        description="Search start time (ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ)"
    )

    end_time: Optional[str] = Field(
        default=None,
        description="Search end time (ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ)"
    )

    class Config:
        """Pydantic configuration"""
        extra = "allow"
        validate_assignment = True
