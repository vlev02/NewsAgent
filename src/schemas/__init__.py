"""Request schema registry for all agents - template-based organization"""

from typing import Type, Dict, Any
from .base import RequestSchema
from .bocha import BochaRequestSchema
from .meta import MetaRequestSchema
from .xunfei import XunfeiRequestSchema
from .qianfan import QianfanRequestSchema
from .hunyuan import HunyuanRequestSchema
from .twitter import TwitterRequestSchema

# Import field collection utilities
from .field_collector import FieldCollector, InteractiveFieldCollector


# Schema registry - maps agent names to their request schema classes
# Like Jinja templates - each agent has its own predefined schema
SCHEMA_REGISTRY: Dict[str, Type[RequestSchema]] = {
    "BOCHA": BochaRequestSchema,
    "META": MetaRequestSchema,
    "XUNFEI": XunfeiRequestSchema,
    "QIANFAN": QianfanRequestSchema,
    "HUNYUAN": HunyuanRequestSchema,
    "TWITTER": TwitterRequestSchema,
}


def get_schema(agent_name: str) -> Type[RequestSchema]:
    """
    Get request schema class for an agent.

    Works like Jinja template lookup - returns the predefined
    schema for the given agent name.

    Args:
        agent_name: Name of the agent (e.g., "BOCHA", "META")

    Returns:
        RequestSchema class for the agent

    Raises:
        KeyError: If agent_name not found in registry
    """
    if agent_name not in SCHEMA_REGISTRY:
        available = ", ".join(SCHEMA_REGISTRY.keys())
        raise KeyError(
            f"No schema found for agent '{agent_name}'. "
            f"Available agents: {available}"
        )
    return SCHEMA_REGISTRY[agent_name]


def validate_request_body(agent_name: str, body: Dict[str, Any]) -> RequestSchema:
    """
    Validate request body against agent's schema.

    Args:
        agent_name: Name of the agent
        body: Request body dictionary to validate

    Returns:
        Validated schema instance

    Raises:
        KeyError: If agent not found
        ValueError: If validation fails (from Pydantic)
    """
    schema_class = get_schema(agent_name)
    return schema_class(**body)


def get_all_schemas() -> Dict[str, Type[RequestSchema]]:
    """
    Get all registered schemas.

    Returns:
        Dictionary of agent_name -> schema class
    """
    return SCHEMA_REGISTRY.copy()


__all__ = [
    "RequestSchema",
    "BochaRequestSchema",
    "MetaRequestSchema",
    "XunfeiRequestSchema",
    "QianfanRequestSchema",
    "HunyuanRequestSchema",
    "TwitterRequestSchema",
    "SCHEMA_REGISTRY",
    "get_schema",
    "validate_request_body",
    "get_all_schemas",
    "FieldCollector",
    "InteractiveFieldCollector",
]
