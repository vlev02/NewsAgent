"""
Utilities package for NewsAgent.

Exposes environment loading helpers, debug logging facilities, and a handful of
utility helpers that were historically shipped in ``src/utils.py``. The original
module was removed during a refactor which meant importing ``src.utils`` no longer
provided the helpers that several agents depend on (``get_api_time_filter``,
``load_jinja_template``, etc.). Re-implementing the helpers here keeps backwards
compatibility and avoids runtime import errors inside agent modules.
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, Optional
from urllib.parse import urlencode

from jinja2 import Template

# Environment loading (must be imported first)
from .env_loader import EnvLoader

# Debug/logging helpers
from .debug_logger import DebugLogger, print_debug_header, print_debug_info

# ---------------------------------------------------------------------------
# Legacy helper implementations (originally in src/utils.py)
# ---------------------------------------------------------------------------

TIME_FILTER_MAPPING: Dict[str, Dict[str, Any]] = {
    "oneDay": {"days": 1, "description": "最近24小时"},
    "threeDays": {"days": 3, "description": "最近三天"},
    "oneWeek": {"days": 7, "description": "最近一周"},
    "twoWeeks": {"days": 14, "description": "最近两周"},
    "oneMonth": {"days": 30, "description": "最近一月"},
    "threeMonths": {"days": 90, "description": "最近三月"},
    "sixMonths": {"days": 180, "description": "最近半年"},
    "oneYear": {"days": 365, "description": "最近一年"},
}


def _ordered_time_filters() -> Iterable[tuple[str, Dict[str, Any]]]:
    """Internal helper to yield filters ordered by duration."""
    return sorted(
        TIME_FILTER_MAPPING.items(),
        key=lambda item: item[1]["days"],
    )


def get_api_time_filter(days_back: Optional[int], default: str = "oneWeek") -> str:
    """
    Convert a ``days_back`` integer into the closest API-friendly time filter key.

    Args:
        days_back: Number of days to look back. If ``None`` we fall back to ``default``.
        default: Fallback filter key when ``days_back`` is not provided.

    Returns:
        String identifier understood by the REST agents (e.g., ``oneDay``, ``oneWeek``).
    """
    if days_back is None or days_back <= 0:
        return default

    for key, meta in _ordered_time_filters():
        if days_back <= meta["days"]:
            return key
    return "oneYear"


def get_time_description(days_back: Optional[int]) -> str:
    """
    Generate a human-friendly description for ``days_back`` (in Chinese for parity
    with the original implementation used in templates).
    """
    if days_back is None or days_back <= 0:
        return "最近一周"

    for key, meta in _ordered_time_filters():
        if days_back <= meta["days"]:
            return meta["description"]
    return TIME_FILTER_MAPPING["oneYear"]["description"]


def build_query_string(params: Dict[str, Any]) -> str:
    """Build a URL query string while skipping ``None`` values."""
    clean_params = {k: v for k, v in params.items() if v is not None}
    return urlencode(clean_params, doseq=True)


def load_jinja_template(path: str) -> Template:
    """Load a Jinja2 template from disk."""
    template_path = Path(path)
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    return Template(template_path.read_text(encoding="utf-8"))


def normalize_json_response(data: Any) -> Any:
    """
    Recursively convert objects that are not JSON serializable (e.g., timedelta)
    into a friendly representation so they can be logged or stored.
    """
    if isinstance(data, dict):
        return {k: normalize_json_response(v) for k, v in data.items()}
    if isinstance(data, list):
        return [normalize_json_response(item) for item in data]
    if isinstance(data, timedelta):
        return data.total_seconds()
    return data


__all__ = [
    "EnvLoader",
    "DebugLogger",
    "print_debug_header",
    "print_debug_info",
    "TIME_FILTER_MAPPING",
    "get_api_time_filter",
    "get_time_description",
    "build_query_string",
    "load_jinja_template",
    "normalize_json_response",
]
