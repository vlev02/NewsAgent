"""Utility functions for the pipeline"""

from datetime import datetime, timedelta
from typing import Dict, Any

# Time filter mappings from uniform days_back to API-specific formats
TIME_FILTER_MAPPING = {
    1: {
        "BOCHA": "oneDay",
        "QIANFAN": "week",  # Baidu doesn't have "day", use closest
        "XUNFEI": "24小时内",
        "HUNYUAN": "最近一天",
        "META": "最近1天",
        "TWITTER": 1  # Days to subtract from now
    },
    7: {
        "BOCHA": "oneWeek",
        "QIANFAN": "week",
        "XUNFEI": "最近一周",
        "HUNYUAN": "最近一周",
        "META": "最近1周",
        "TWITTER": 7
    },
    30: {
        "BOCHA": "oneMonth",
        "QIANFAN": "month",
        "XUNFEI": "最近一个月",
        "HUNYUAN": "最近一个月",
        "META": "最近1月",
        "TWITTER": 30
    },
    365: {
        "BOCHA": "oneYear",
        "QIANFAN": "semiyear",
        "XUNFEI": "最近一年",
        "HUNYUAN": "最近一年",
        "META": "最近1年",
        "TWITTER": 365
    }
}

# Human-readable time descriptions
TIME_DESCRIPTIONS = {
    1: "最近一天",
    7: "最近一周",
    30: "最近一个月",
    365: "最近一年"
}


def get_api_time_filter(days_back: int, agent_name: str) -> Any:
    """
    Get API-specific time filter value.

    Args:
        days_back: Number of days back (1, 7, 30, 365)
        agent_name: Name of the agent

    Returns:
        API-specific time filter value
    """
    # Find closest matching days_back
    closest_key = min(TIME_FILTER_MAPPING.keys(), key=lambda x: abs(x - days_back))
    return TIME_FILTER_MAPPING[closest_key].get(agent_name, TIME_FILTER_MAPPING[closest_key].get(7))


def get_time_description(days_back: int) -> str:
    """Get human-readable time description"""
    closest_key = min(TIME_DESCRIPTIONS.keys(), key=lambda x: abs(x - days_back))
    return TIME_DESCRIPTIONS[closest_key]


def get_twitter_start_time(days_back: int) -> str:
    """Get Twitter API start_time parameter"""
    start_date = datetime.utcnow() - timedelta(days=days_back)
    return start_date.isoformat() + "Z"


def build_query_string(fields: list, topics: list, separator: str = " ") -> str:
    """
    Build a simple keyword query string.

    Args:
        fields: List of field names
        topics: List of topic names
        separator: Separator between keywords

    Returns:
        Combined query string
    """
    all_terms = fields + topics
    return separator.join(all_terms)


def normalize_json_response(response_text: str) -> Dict[str, Any]:
    """
    Extract and normalize JSON from response text.

    Handles markdown code blocks and direct JSON.

    Args:
        response_text: Text possibly containing JSON

    Returns:
        Parsed JSON as dict
    """
    import json
    import re

    # Try markdown code block
    json_match = re.search(r'```json\s*(.+?)\s*```', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try direct JSON
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # Try parsing entire text
    try:
        return json.loads(response_text.strip())
    except json.JSONDecodeError as e:
        raise ValueError(f"Could not extract JSON from response: {e}")


def load_jinja_template(template_path: str):
    """Load a Jinja2 template from file"""
    from jinja2 import Template

    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return Template(content)
