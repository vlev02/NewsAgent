# Request Schemas - Agent-Specific Request Body Validation

This module provides **template-style** Pydantic request schemas for each agent, ensuring request bodies conform to agent-specific API requirements.

## Overview

Each agent has its own predefined schema that validates:
- Required fields
- Field types
- Enum values (e.g., `freshness: Literal["oneDay", "oneWeek", ...]`)
- Value ranges (e.g., `count: int(ge=1, le=100)`)

Think of these like Jinja templates - each agent has a pre-defined template for what its request should look like.

## Structure

```
src/schemas/
├── __init__.py          # Registry and loader
├── base.py              # Base RequestSchema class
├── bocha.py             # BOCHA-specific schema
├── meta.py              # META-specific schema
├── xunfei.py            # Xunfei-specific schema
├── qianfan.py           # Qianfan-specific schema
├── hunyuan.py           # Hunyuan-specific schema
├── twitter.py           # Twitter-specific schema
└── README.md            # This file
```

## Usage Examples

### Get a Schema

```python
from src.schemas import get_schema

# Get BOCHA schema class
bocha_schema = get_schema("BOCHA")

# Get META schema class
meta_schema = get_schema("META")
```

### Validate a Request Body

```python
from src.schemas import validate_request_body

# Validate BOCHA request
body = {
    "query": "artificial intelligence",
    "freshness": "oneWeek",
    "count": 10,
    "summary": True
}

validated = validate_request_body("BOCHA", body)
print(validated.validate_and_get_dict())  # Returns validated dict
```

### Handle Validation Errors

```python
from src.schemas import validate_request_body
from pydantic import ValidationError

try:
    invalid_body = {
        "query": "test",
        "freshness": "invalidValue",  # Not in Literal enum
        "count": 150,  # Exceeds max of 100
        "summary": True
    }
    validate_request_body("BOCHA", invalid_body)
except ValidationError as e:
    print(f"Validation failed: {e}")
    for error in e.errors():
        print(f"  - {error['loc']}: {error['msg']}")
```

### Get All Registered Schemas

```python
from src.schemas import get_all_schemas

schemas = get_all_schemas()
print(schemas.keys())
# Output: dict_keys(['BOCHA', 'META', 'XUNFEI', 'QIANFAN', 'HUNYUAN', 'TWITTER'])
```

## Agent Schemas

### BOCHA Schema (BochaRequestSchema)

**Validates:**
- `query` (str): Search keywords (1-1000 chars)
- `freshness` (Literal): `oneDay`, `oneWeek`, `oneMonth`, `oneYear`
- `count` (int): 1-100 results
- `summary` (bool): Include AI summary

### META Schema (MetaRequestSchema)

**Validates:**
- `query` (str): Search keywords (1-1000 chars)
- `scope` (Literal): `webpage`, `news`, `academic`, `patent`, `arxiv`
- `size` (int): 1-100 results
- `includeRawContent` (bool): Include raw HTML/content

### XUNFEI Schema (XunfeiRequestSchema)

**Validates:**
- `model` (Literal): `4.0Ultra`, `4.0`, `3.5`
- `query` (str): Question/search (1-2000 chars)
- `temperature` (float): 0.0-1.0
- `max_tokens` (int): 100-8000
- `search_mode` (Literal): `deep`, `web`, `document`

### QIANFAN Schema (QianfanRequestSchema)

**Validates:**
- `model` (Literal): `deepseek-r1`, `ernie-4.0`, `ernie-3.5`
- `query` (str): Question/search (1-2000 chars)
- `search_source` (Literal): `baidu_search_v2`, `baidu_search_v1`
- `enable_reasoning` (bool): Enable reasoning
- `temperature` (float): 0.0-1.0
- `top_p` (float): 0.0-1.0
- `max_completion_tokens` (int): 100-32000

### HUNYUAN Schema (HunyuanRequestSchema)

**Validates:**
- `model` (Literal): `hunyuan-turbo`, `hunyuan-pro`, `hunyuan-standard`
- `query` (str): Question/search (1-2000 chars)
- `temperature` (float): 0.0-1.0
- `enable_enhancement` (bool): Response enhancement
- `search_info` (bool): Include search info

### TWITTER Schema (TwitterRequestSchema)

**Validates:**
- `query` (str): Search query (1-512 chars)
- `sort_order` (Literal): `recency`, `relevance`, `engagement`
- `max_results` (int): 10-100
- `start_time` (Optional[str]): ISO 8601 format
- `end_time` (Optional[str]): ISO 8601 format

## Integration

Agents should validate request bodies before making API calls:

```python
from src.schemas import validate_request_body

# In Agent.call_api():
body = {
    "query": query,
    "freshness": time_filter,
    "count": request.max_results,
    "summary": request.include_ai_summary
}

# Validate and convert to dict
validated_schema = validate_request_body(self.config.agent_name, body)
validated_body = validated_schema.validate_and_get_dict()

# Use validated_body for API call
return handle_api_request(..., json_body=validated_body, ...)
```

## Benefits

1. **Type Safety**: Catch invalid requests before API calls
2. **Clear Errors**: Pydantic provides detailed validation error messages
3. **Self-Documenting**: Schemas serve as request format documentation
4. **Extensible**: Easy to add new agents or modify existing schemas
5. **Consistent**: All agents follow same validation pattern
6. **Template-Based**: Like Jinja templates, each agent has a predefined format
