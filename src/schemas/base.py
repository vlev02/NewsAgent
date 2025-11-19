"""Base request schema for all agents"""

from typing import Any
from pydantic import BaseModel


class RequestSchema(BaseModel):
    """Base request schema with common validation rules"""

    class Config:
        """Pydantic configuration"""
        extra = "allow"  # Allow extra fields for agent-specific params
        validate_assignment = True

    def validate_and_get_dict(self) -> dict[str, Any]:
        """
        Validate and convert schema to dictionary.

        Returns:
            Dictionary representation of validated request

        Raises:
            ValueError: If validation fails
        """
        return self.model_dump(exclude_none=True)
