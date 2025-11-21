"""
Utils package for NewsAgent.

Includes utility functions and debug/fake response system components.
"""

# Environment loading (must be imported first)
from .env_loader import EnvLoader

# Import new modules from subpackage
from .fake_response_manager import FakeResponseManager, fake_response_manager
from .debug_logger import DebugLogger, print_debug_header, print_debug_info

# Import original utils functions from parent module
# Note: Using absolute import from parent src.utils module
import sys
from pathlib import Path

# Access the original utils.py module
utils_module_path = Path(__file__).parent.parent / "utils.py"
if utils_module_path.exists():
    try:
        # Import directly from the utils.py file
        import importlib.util
        spec = importlib.util.spec_from_file_location("_utils_module", utils_module_path)
        _utils_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_utils_module)

        # Re-export the functions
        TIME_FILTER_MAPPING = _utils_module.TIME_FILTER_MAPPING
        get_api_time_filter = _utils_module.get_api_time_filter
        get_time_description = _utils_module.get_time_description
        build_query_string = _utils_module.build_query_string
        load_jinja_template = _utils_module.load_jinja_template
        normalize_json_response = _utils_module.normalize_json_response
    except Exception:
        # If import fails, functions will need to be imported directly from utils.py
        pass

__all__ = [
    # Environment loading
    "EnvLoader",
    # New fake response system
    "FakeResponseManager",
    "fake_response_manager",
    "DebugLogger",
    "print_debug_header",
    "print_debug_info",
    # Original utils functions
    "TIME_FILTER_MAPPING",
    "get_api_time_filter",
    "get_time_description",
    "build_query_string",
    "load_jinja_template",
    "normalize_json_response",
]
