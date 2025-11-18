"""
Decorators module for NewsAgent pipeline.

Provides utilities for handling API responses, caching, and debugging.
"""

from .response_handler import handle_api_request, fake_response_handler

__all__ = [
    "handle_api_request",  # Primary: Unified request handler (recommended)
    "fake_response_handler",  # Legacy: Decorator wrapper (for backward compatibility)
]
