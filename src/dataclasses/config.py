"""Backward compatibility shim for AgentConfig.

AgentConfig now lives in src.agents.config to keep configuration code alongside
the agent implementations. Importing from src.dataclasses.config continues to
work for legacy callers.
"""

from src.agents.config import AgentConfig, load_agents_from_yaml, AGENT_CONFIGS

__all__ = ["AgentConfig", "load_agents_from_yaml", "AGENT_CONFIGS"]
