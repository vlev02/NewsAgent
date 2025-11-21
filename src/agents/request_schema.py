"""Base request schema for all agents - reusable across all agent implementations"""

from typing import Any
from pydantic import BaseModel


class RequestSchema(BaseModel):
    """
    Base request schema with common validation rules.

    All agent-specific RequestSchema classes should inherit from this base class.
    This provides a unified interface for request validation across all agents.

    Features:
    - Flexible field validation (extra fields allowed for agent-specific params)
    - Assignment validation to catch field errors at assignment time
    - Common method for converting to validated dictionary
    """

    class Config:
        """Pydantic configuration"""
        extra = "allow"  # Allow extra fields for agent-specific params
        validate_assignment = True

    def validate_and_get_dict(self) -> dict[str, Any]:
        """
        Validate and convert schema to dictionary.

        Returns:
            Dictionary representation of validated request with None values excluded

        Raises:
            ValueError: If validation fails
        """
        return self.model_dump(exclude_none=True)


class TemplateSchema(BaseModel):
    """
    Base template schema for LLM agents using Jinja2 templates.

    All agent-specific TemplateSchema classes should inherit from this base class.
    This provides a unified interface for template variable validation.

    Features:
    - Flexible field validation (extra fields allowed for agent-specific template vars)
    - Assignment validation to catch field errors at assignment time
    - Common method for converting to validated dictionary
    - Template path configuration

    Used by LLM_SEARCH agents that use Jinja2 templates for dynamic prompt generation.
    """

    class Config:
        """Pydantic configuration"""
        extra = "allow"  # Allow extra fields for agent-specific template variables
        validate_assignment = True

    def validate_and_get_dict(self) -> dict[str, Any]:
        """
        Validate and convert template schema to dictionary.

        Returns:
            Dictionary representation of validated template variables with None values excluded

        Raises:
            ValueError: If validation fails
        """
        return self.model_dump(exclude_none=True)
