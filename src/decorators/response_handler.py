"""
Response Handler Decorator

Wraps agent API calls to handle fake response caching and user interaction.
Uses MD5-based storage for efficient lookup and single-file replacement.
"""

import functools
from typing import Callable, Any, Optional

from src.debug_config import DebugConfig
from src.utils.fake_response_manager import fake_response_manager
from src.utils.debug_logger import DebugLogger, print_debug_info, print_debug_warning

logger = DebugLogger(__name__)


def fake_response_handler(
    agent_name: str,
    url: str,
    method: str = "POST",
    description: str = "default"
):
    """
    Decorator to handle fake response caching for agent API calls.

    This decorator:
    1. Checks if fake responses are enabled
    2. Generates MD5 hash of (url, method, description)
    3. Tries to load cached response
    4. If found, optionally asks user, then returns cached response
    5. If not found, calls real API and optionally caches result
    6. Logs operations if DEBUG is enabled

    Usage:
        @fake_response_handler(agent_name="BOCHA",
                               url="https://api.bocha.ai/search",
                               method="POST",
                               description="default")
        def submit_and_parse(self, query):
            # Real API call logic
            return response

    Args:
        agent_name: Name of the agent (BOCHA, XUNFEI, etc.)
        url: API endpoint URL
        method: HTTP method (default: POST)
        description: Description for this specific request (default: "default")

    Returns:
        Decorated function that handles caching
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, query: Any, *args, **kwargs) -> dict:
            # Check if fake responses are disabled
            if not DebugConfig.fake_response_enabled:
                if DebugConfig.log_decorator_calls:
                    logger.info(f"Fake responses disabled, calling real API: {agent_name}")
                return func(self, query, *args, **kwargs)

            # Generate hash for this specific request
            md5_hash = fake_response_manager.generate_hash(url, method, description)

            if DebugConfig.log_decorator_calls:
                logger.debug(f"Checking for cached response: {agent_name}/{md5_hash}")

            # Try to load cached response
            cached_response = fake_response_manager.get_response(
                agent_name=agent_name,
                url=url,
                method=method,
                description=description
            )

            if cached_response:
                # Found cached response
                logger.info(f"Using cached response: {agent_name}/{md5_hash}")

                # Ask user if in interactive mode
                if DebugConfig.fake_response_interact and DebugConfig.DEBUG:
                    choice = _ask_user_choice(
                        agent_name=agent_name,
                        url=url,
                        method=method,
                        description=description,
                        md5_hash=md5_hash,
                        cached=True
                    )

                    if choice == 'real':
                        # User chose to call real API instead
                        logger.info("User chose to call real API")
                        response = func(self, query, *args, **kwargs)

                        # Update cache if flag is set
                        if DebugConfig.fake_response_update:
                            _cache_response(
                                agent_name, url, method, description,
                                query, response
                            )
                        return response

                    elif choice == 'update':
                        # User chose to update cache
                        logger.info("User chose to update cache with real API response")
                        response = func(self, query, *args, **kwargs)
                        _cache_response(
                            agent_name, url, method, description,
                            query, response
                        )
                        return response

                    elif choice == 'skip':
                        # Skip interaction for rest of session
                        DebugConfig._skip_interaction_for_session = True
                        return cached_response

                # Return cached response
                return cached_response

            else:
                # No cached response found
                logger.info(f"No cached response found: {agent_name}/{md5_hash}")

                # Ask user if in interactive mode (no cached response)
                if DebugConfig.fake_response_interact and DebugConfig.DEBUG:
                    if not DebugConfig._skip_interaction_for_session:
                        choice = _ask_user_choice(
                            agent_name=agent_name,
                            url=url,
                            method=method,
                            description=description,
                            md5_hash=md5_hash,
                            cached=False
                        )

                        if choice == 'skip':
                            DebugConfig._skip_interaction_for_session = True

                # Call real API
                response = func(self, query, *args, **kwargs)

                # Cache response if update flag is enabled
                if DebugConfig.fake_response_update:
                    _cache_response(
                        agent_name, url, method, description,
                        query, response
                    )

                return response

        return wrapper

    return decorator


def _ask_user_choice(
    agent_name: str,
    url: str,
    method: str,
    description: str,
    md5_hash: str,
    cached: bool = True
) -> str:
    """
    Ask user for choice on response handling.

    Args:
        agent_name: Name of the agent
        url: API endpoint
        method: HTTP method
        description: Description
        md5_hash: MD5 hash of the request
        cached: Whether cached response exists

    Returns:
        User choice: 'fake', 'real', 'update', 'skip'
    """
    print()
    print(f"{'='*70}")
    print(f"Fake Response Interaction - {agent_name}")
    print(f"{'='*70}")
    print(f"Agent:      {agent_name}")
    print(f"URL:        {url}")
    print(f"Method:     {method}")
    print(f"Hash:       {md5_hash}")
    print()

    if cached:
        print("Options:")
        print("  (f)ake   - Use cached response")
        print("  (r)eal   - Call real API")
        print("  (u)pdate - Call real API and update cache")
        print("  (s)kip   - Don't ask again this session")
    else:
        print("No cached response found.")
        print("Options:")
        print("  (c)all   - Call real API (and cache if enabled)")
        print("  (s)kip   - Don't ask again this session")

    while True:
        choice = input("\nYour choice: ").strip().lower()

        if cached:
            if choice in ('f', 'fake'):
                return 'fake'
            elif choice in ('r', 'real'):
                return 'real'
            elif choice in ('u', 'update'):
                return 'update'
            elif choice in ('s', 'skip'):
                return 'skip'
        else:
            if choice in ('c', 'call'):
                return 'call'
            elif choice in ('s', 'skip'):
                return 'skip'

        print("Invalid choice. Please try again.")


def _cache_response(
    agent_name: str,
    url: str,
    method: str,
    description: str,
    query: Any,
    response: dict
) -> bool:
    """
    Cache an API response.

    Args:
        agent_name: Name of the agent
        url: API endpoint
        method: HTTP method
        description: Description
        query: The QueryRequest object
        response: The response to cache

    Returns:
        True if successful, False otherwise
    """
    try:
        # Extract request parameters from query object
        request_body = {
            "query_fields": getattr(query, 'query_fields', []),
            "query_topics": getattr(query, 'query_topics', []),
            "source_agents": getattr(query, 'source_agents', []),
            "days_back": getattr(query, 'days_back', 7),
            "max_results": getattr(query, 'max_results', 10),
            "language": getattr(query, 'language', 'en'),
        }

        # Update or save response
        if fake_response_manager.response_exists(agent_name, url, method, description):
            success = fake_response_manager.update_response(
                agent_name=agent_name,
                url=url,
                method=method,
                description=description,
                request_body=request_body,
                response_body=response
            )
            logger.info(f"Updated cached response: {agent_name}/{description}")
        else:
            success = fake_response_manager.save_response(
                agent_name=agent_name,
                url=url,
                method=method,
                description=description,
                request_body=request_body,
                response_body=response,
                notes="Auto-cached from API call"
            )
            logger.info(f"Saved new cached response: {agent_name}/{description}")

        return success

    except Exception as e:
        logger.error(f"Failed to cache response: {e}")
        return False
