"""Data Manager module

Provides a unified interface for managing request logs and response items.
Decoupled from agent manager - can be used independently.

Public API:
- get_data_manager(): Get the global singleton DataManager instance
- DataModelType: Enum of available data models
- Models: RequestModel, ResponseItem
- AgentDataWrapper: Mixin for agents to integrate with DataManager

Usage:
    from src.data_manager import get_data_manager, DataModelType, AgentDataWrapper

    # In agent class
    class MyAgent(SearchAgent, AgentDataWrapper):
        ...

    # In application code
    dm = get_data_manager()
    models = dm.models()
    report = dm.explore(DataModelType.REQUEST)
    request_data = dm.retrieve(DataModelType.REQUEST, case_key)
    request_id = dm.record(DataModelType.REQUEST, request_dict)
"""

from .models import RequestModel, ResponseItem, DataModelType
from .manager import DataManager, get_data_manager
from .agent_wrapper import AgentDataWrapper
from .config import create_test_config

__all__ = [
    "RequestModel",
    "ResponseItem",
    "DataModelType",
    "DataManager",
    "get_data_manager",
    "AgentDataWrapper",
    "create_test_config",
]
