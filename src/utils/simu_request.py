"""
SimuRequest - Unified Request Caching System

A lightweight, decorator-based API response caching system for offline development
and testing. Uses two core flags (simu_call, update_response) with a simplified
4-scenario behavior table.

Features:
    - Decorator: @SimuRequest.simu_request
    - Runtime Control: SimuRequest.update_behaviors()
    - Status: SimuRequest.status()
    - All private helpers encapsulated in the class
    - Complete request metadata and timestamp capture

MD5 hashing based on function name and class name (no extra params needed).
Configuration from config/simu_call.yaml (relative paths converted to absolute).

Cache Storage:
    Path: {PROJECT_ROOT}/{persist_dir}/{class_name}/{function_name}_{md5}.json

    File Structure:
    {
        "response": {...},           # API response
        "request": {                 # Complete request metadata
            "url": "...",
            "method": "POST",
            "json": {...},          # Request body
            "headers": {...},       # Request headers
            "timeout": 30
        },
        "timestamp": "2025-11-21T12:34:56.789012Z"  # UTC timestamp
    }

Usage:
    from src.utils.simu_request import SimuRequest

    # Apply decorator
    @SimuRequest.simu_request
    def submit_request(self):
        request_args = {
            "url": self.api_endpoint,
            "method": "POST",
            "json": self.request_body,
            "headers": self.get_header_dict(),
            "timeout": 30
        }
        self._last_request_metadata = request_args.copy()
        response = requests.request(**request_args)
        return response

    # Update flags at runtime
    SimuRequest.update_behaviors(simu_call=1, update_response=0)

    # View current configuration
    SimuRequest.status()
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional
from functools import wraps

import yaml


class SimuRequest:
    """Unified SimuRequest caching system with all logic encapsulated.

    Simplified behavior table:
    | simu_call | update_response | Cache Hit? | Behavior              |
    |-----------|-----------------|------------|----------------------|
    | -         | -               | 0          | real call, auto save |
    | -         | 1               | 1          | real call, auto save |
    | 0         | 0               | 1          | real call, no save   |
    | 1         | 0               | 1          | simu call, no save   |

    Logic:
    - Cache miss (no hit): Always real call + auto-save
    - Cache hit with update_response=1: Real call + auto-save (refresh)
    - Cache hit with simu_call=0: Real call, no save
    - Cache hit with simu_call=1: Use simulation (cached response)
    """

    # Class-level configuration singleton
    _instance = None
    _config: Dict[str, Any] = {}

    def __init__(self):
        """Initialize configuration from simu_call.yaml"""
        if not SimuRequest._config:
            self._load_config()

    def __new__(cls):
        """Ensure singleton pattern for configuration"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def _load_config() -> None:
        """Load configuration from simu_call.yaml (private)"""
        config_path = Path(__file__).parent.parent.parent / "config" / "simu_call.yaml"

        if not config_path.exists():
            # Use defaults if config doesn't exist
            SimuRequest._config = {
                "simu_call": 0,
                "update_response": 0,
                "persist_dir": "data/simu_responses",
                "log_calls": 1,
            }
            return

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded = yaml.safe_load(f) or {}
                # Filter out comments and extract only relevant config
                SimuRequest._config = {
                    "simu_call": loaded.get("simu_call", 0),
                    "update_response": loaded.get("update_response", 0),
                    "persist_dir": loaded.get("persist_dir", "data/simu_responses"),
                    "log_calls": loaded.get("log_calls", 1),
                }
        except Exception as e:
            print(f"Warning: Failed to load simu_call.yaml: {e}")
            SimuRequest._config = {
                "simu_call": 0,
                "update_response": 0,
                "persist_dir": "data/simu_responses",
                "log_calls": 1,
            }

    @staticmethod
    def _get_config_value(key: str, default: Any = None) -> Any:
        """Get configuration value (private)"""
        if not SimuRequest._config:
            SimuRequest._load_config()
        return SimuRequest._config.get(key, default)

    @staticmethod
    def _set_config_value(key: str, value: Any) -> None:
        """Set configuration value in memory (private)"""
        if not SimuRequest._config:
            SimuRequest._load_config()
        if key in SimuRequest._config:
            SimuRequest._config[key] = value

    @staticmethod
    def _generate_md5_hash(class_name: str, function_name: str) -> str:
        """Generate MD5 hash from class name and function name (private)

        Args:
            class_name: Name of the class
            function_name: Name of the function

        Returns:
            MD5 hash string (first 16 chars for readability)
        """
        combined = f"{class_name}:{function_name}"
        hash_obj = hashlib.md5(combined.encode())
        return hash_obj.hexdigest()[:16]

    @staticmethod
    def _get_cache_path(
        class_name: str,
        function_name: str,
        persist_dir: str = "data/simu_responses"
    ) -> Path:
        """Generate absolute cache file path for a function call (private)

        Converts relative paths to absolute by combining with project root.

        Format: {PROJECT_ROOT}/{persist_dir}/{class_name}/{function_name}_{md5}.json

        Args:
            class_name: Name of the class containing the function
            function_name: Name of the function
            persist_dir: Relative path to cache storage (from project root)

        Returns:
            Path object pointing to absolute cache file path
        """
        project_root = Path(__file__).parent.parent.parent
        persist_path = project_root / persist_dir
        class_path = persist_path / class_name
        md5_hash = SimuRequest._generate_md5_hash(class_name, function_name)
        cache_file = class_path / f"{function_name}_{md5_hash}.json"

        return cache_file

    @staticmethod
    def _load_cached_response(cache_path: Path) -> Optional[Dict[str, Any]]:
        """Load cached response from file (private)

        Args:
            cache_path: Path to cache file

        Returns:
            Cached response dict or None if not found
        """
        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                return cached_data.get('response')
        except Exception as e:
            print(f"Warning: Failed to load cache from {cache_path}: {e}")
            return None

    @staticmethod
    def _save_cached_response(
        cache_path: Path,
        response: Dict[str, Any],
        request_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Save response to cache file with complete request metadata and timestamp (private)

        Cache file structure:
            {
                "response": {...},
                "request": {...},
                "timestamp": "2025-11-21T12:34:56.789012Z"
            }

        Args:
            cache_path: Path to cache file
            response: Response dict to cache
            request_metadata: Complete request metadata including url, method, headers, body, timeout, etc.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            cache_path.parent.mkdir(parents=True, exist_ok=True)

            cache_data = {
                "response": response,
                "request": request_metadata or {},
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }

            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"Warning: Failed to save cache to {cache_path}: {e}")
            return False

    @staticmethod
    def _call_and_save(
        func: Callable,
        self: Any,
        args: tuple,
        kwargs: dict,
        cache_path: Path,
        log_calls: bool,
        request_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Helper to call real API and save response to cache (private)

        Args:
            func: Function to call
            self: Instance object (for extracting request info)
            args: Function arguments
            kwargs: Function keyword arguments
            cache_path: Path to cache file
            log_calls: Whether to log operations
            request_metadata: Complete request metadata (url, method, headers, body, timeout, etc.)
        """
        try:
            response = func(self, *args, **kwargs)
        except Exception as e:
            if log_calls:
                print(f"  → API call failed: {e}")
            raise

        # Auto-save response with metadata
        if response is not None:
            # Use provided metadata or build from agent object
            if request_metadata is None:
                request_metadata = {}

                # Try to get stored request metadata from agent
                if hasattr(self, '_last_request_metadata'):
                    request_metadata = getattr(self, '_last_request_metadata', {}).copy()

                # Fallback: build from agent attributes if metadata not stored
                if not request_metadata:
                    request_metadata['body'] = getattr(self, 'request_body', None)
                    if hasattr(self, 'get_header_dict'):
                        try:
                            request_metadata['headers'] = self.get_header_dict()
                        except Exception:
                            pass

            success = SimuRequest._save_cached_response(
                cache_path,
                response,
                request_metadata=request_metadata
            )
            if log_calls:
                if success:
                    print(f"  → Saved to cache")
                else:
                    print(f"  → Failed to save cache")

        return response

    @staticmethod
    def simu_request(func: Callable) -> Callable:
        """Decorator for simulated API calls with caching (PUBLIC)

        Behavior table (simplified):
        | simu_call | update_response | Cache Hit? | Behavior              |
        |-----------|-----------------|------------|----------------------|
        | -         | -               | 0          | real call, auto save |
        | -         | 1               | 1          | real call, auto save |
        | 0         | 0               | 1          | real call, no save   |
        | 1         | 0               | 1          | simu call, no save   |

        MD5 hash is generated from class name and function name.

        Flags:
        - simu_call=1: Use cached response if available
        - update_response=1: Refresh cache from real API (always call real API)

        Usage:
            @SimuRequest.simu_request
            def submit_request(self, query, request):
                response = requests.post(...)
                return response

        Args:
            func: Function to decorate (expects self as first param)

        Returns:
            Decorated function with caching behavior
        """

        @wraps(func)
        def wrapper(self, *args, **kwargs) -> Dict[str, Any]:
            # Get configuration
            simu_call_enabled = SimuRequest._get_config_value("simu_call", 0)
            update_response_enabled = SimuRequest._get_config_value("update_response", 0)
            persist_dir = SimuRequest._get_config_value("persist_dir", "data/simu_responses")
            log_calls = SimuRequest._get_config_value("log_calls", 1)

            # Get class name and function name
            class_name = self.__class__.__name__
            function_name = func.__name__

            # Generate cache path
            cache_path = SimuRequest._get_cache_path(class_name, function_name, persist_dir)
            md5_hash = SimuRequest._generate_md5_hash(class_name, function_name)

            if log_calls:
                print(f"[SimuCall] {class_name}.{function_name} (hash: {md5_hash})")

            # Check if cache exists
            cached_response = SimuRequest._load_cached_response(cache_path)
            cache_hit = cached_response is not None

            # Logic based on behavior table:
            # 1. Cache miss (0): Always real call + auto-save
            if not cache_hit:
                if log_calls:
                    print(f"  → No cache found, calling real API")
                response = SimuRequest._call_and_save(func, self, args, kwargs, cache_path, log_calls)
                # Wrap response with response_type metadata
                return {
                    "response": response,
                    "response_type": "real_call"
                }

            # 2. Cache hit with update_response=1: Real call + auto-save (refresh)
            if cache_hit and update_response_enabled:
                if log_calls:
                    print(f"  → Cache found, update_response=1, refreshing from real API")
                response = SimuRequest._call_and_save(func, self, args, kwargs, cache_path, log_calls)
                # Wrap response with response_type metadata
                return {
                    "response": response,
                    "response_type": "real_call"
                }

            # 3. Cache hit with simu_call=0: Real call, no save
            if cache_hit and not simu_call_enabled:
                if log_calls:
                    print(f"  → Cache found, simu_call=0, calling real API (no save)")
                try:
                    response = func(self, *args, **kwargs)
                except Exception as e:
                    if log_calls:
                        print(f"  → API call failed: {e}")
                    raise
                # Wrap response with response_type metadata
                return {
                    "response": response,
                    "response_type": "real_call"
                }

            # 4. Cache hit with simu_call=1: Use simulation (cached response)
            if cache_hit and simu_call_enabled:
                if log_calls:
                    print(f"  → Using cached response")
                # Wrap response with response_type metadata
                return {
                    "response": cached_response,
                    "response_type": "cached_response"
                }

            # Fallback (should not reach here)
            return {
                "response": func(self, *args, **kwargs),
                "response_type": "real_call"
            }

        return wrapper

    @staticmethod
    def update_behaviors(
        simu_call: int = None,
        update_response: int = None,
        log_calls: int = None,
        verbose: bool = True
    ) -> None:
        """Update SimuCall behavior flags at runtime (PUBLIC)

        Args:
            simu_call: 1 = use cache, 0 = use API (optional)
            update_response: 1 = update cache, 0 = no update (optional)
            log_calls: 1 = enable logging, 0 = disable logging (optional)
            verbose: Print confirmation message (default: True)

        Example:
            SimuRequest.update_behaviors(simu_call=1, update_response=0)
        """
        changes = []

        if simu_call is not None:
            SimuRequest._set_config_value("simu_call", simu_call)
            changes.append(f"simu_call={simu_call}")

        if update_response is not None:
            SimuRequest._set_config_value("update_response", update_response)
            changes.append(f"update_response={update_response}")

        if log_calls is not None:
            SimuRequest._set_config_value("log_calls", log_calls)
            changes.append(f"log_calls={log_calls}")

        if verbose and changes:
            print(f"✓ Behaviors updated: {', '.join(changes)}")

    @staticmethod
    def status() -> Dict[str, Any]:
        """Display and return current SimuCall configuration (PUBLIC)

        Returns:
            Dict with current configuration (simu_call, update_response, log_calls, persist_dir)
            persist_dir is returned as absolute path

        Example:
            config = SimuRequest.status()
            print(config)
        """
        # Get relative path from config
        relative_persist_dir = SimuRequest._get_config_value("persist_dir")

        # Convert to absolute path
        project_root = Path(__file__).parent.parent.parent
        absolute_persist_dir = str(project_root / relative_persist_dir)

        config_dict = {
            "simu_call": SimuRequest._get_config_value("simu_call"),
            "update_response": SimuRequest._get_config_value("update_response"),
            "persist_dir": absolute_persist_dir,
            "log_calls": SimuRequest._get_config_value("log_calls"),
        }

        print("\n" + "=" * 70)
        print("SimuCall Configuration")
        print("=" * 70)
        print(f"simu_call:       {config_dict['simu_call']:<2} (0=real API, 1=cached)")
        print(f"update_response: {config_dict['update_response']:<2} (0=no save, 1=save)")
        print(f"log_calls:       {config_dict['log_calls']:<2} (0=quiet, 1=verbose)")
        print(f"persist_dir:     {config_dict['persist_dir']}")
        print("=" * 70)

        # Show current mode
        simu_call = config_dict["simu_call"]
        update_response = config_dict["update_response"]

        if update_response:
            mode = "🔄 REFRESH (real API + save)"
        elif simu_call:
            mode = "📦 SIMULATION (cached responses)"
        else:
            mode = "🌐 LIVE API (real API)"

        print(f"\nMode: {mode}\n")

        return config_dict

    @staticmethod
    def reload() -> None:
        """Reload configuration from file (PUBLIC)

        Clears the in-memory configuration and reloads from simu_call.yaml.
        """
        SimuRequest._config = {}
        SimuRequest._instance = None
        SimuRequest._load_config()


# For backward compatibility: keep old function signatures available
def simu_request(func: Callable) -> Callable:
    """Backward compatibility wrapper for @simu_request decorator

    Use @SimuRequest.simu_request instead.
    """
    return SimuRequest.simu_request(func)


# Backward compatibility for SimuCallConfig (deprecated)
class SimuCallConfig:
    """Backward compatibility class (DEPRECATED)

    Use SimuRequest instead.
    """

    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return SimuRequest._get_config_value(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value in memory"""
        SimuRequest._set_config_value(key, value)
        if SimuRequest._get_config_value("log_calls"):
            print(f"[SimuCall Config] {key} = {value}")

    @classmethod
    def reload(cls):
        """Reload configuration from file"""
        SimuRequest.reload()
        return cls()

    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """Get current configuration as dictionary"""
        return SimuRequest.status()
