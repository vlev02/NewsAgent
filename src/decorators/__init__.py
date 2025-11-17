"""
Decorators module for NewsAgent pipeline.

Provides decorators for handling API responses, caching, and debugging.
"""

from .response_handler import fake_response_handler

__all__ = [
    "fake_response_handler",
]
