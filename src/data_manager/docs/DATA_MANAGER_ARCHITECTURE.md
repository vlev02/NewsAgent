# Data Manager Architecture

## Overview

Independent data management system decoupled from agents and agent_manager. Handles logging of API requests, structured queries, and search results with automatic cascade deletion.

## Module Structure

```
src/data_manager/
├── __init__.py           # Public API exports
├── models.py             # 3 dataclass models
├── config.py             # YAML configuration loader
├── manager.py            # DataManager singleton
└── storage.py            # SQLite backend implementation

config/
└── data_manager.yaml     # Configuration (all defaults here)
```

## Data Models

### 1. RequestModel
Complete raw API request and response log (root record).

```python
@dataclass
class RequestModel:
    request_id: str          # UUID
    agent_name: str
    timestamp: datetime

    # Raw API request
    url: str
    method: str
    headers: Dict[str, str]
    body: Dict[str, Any]

    # Raw API response
    raw_response: Dict[str, Any]
    http_status: int

    # Metrics
    execution_time_ms: int
    success: bool
    error_message: Optional[str]
```

### 2. QueryModel
Structured query information (cascade to RequestModel).

```python
@dataclass
class QueryModel:
    query_id: str                    # UUID
    request_id: str                  # FK to RequestModel
    agent_name: str
    timestamp: datetime

    # Parsed common fields (normalized across all agents)
    query_keywords: List[str]
    query_topics: List[str]
    days_back: Optional[int]
    time_filter: Optional[str]
    max_results: Optional[int]
    language: Optional[str]

    # Agent-specific params (raw)
    agent_specific_params: Dict[str, Any]
    raw_query_body: Dict[str, Any]
```

### 3. ResponseItem
Single search result (cascade to QueryModel).

```python
@dataclass
class ResponseItem:
    item_id: str                     # UUID
    query_id: str                    # FK to QueryModel
    agent_name: str
    timestamp: datetime

    # Search result fields
    title: str
    content: str
    source_url: str
    source_name: str

    # Metadata
    category: Optional[str]
    key_entities: List[str]
    relevance_score: Optional[float]
    significance: Optional[str]
    agent_metadata: Dict[str, Any]
```

## Public API

### Singleton Access
```python
from src.data_manager import get_data_manager

dm = get_data_manager()  # Always returns same instance
```

### List Models
```python
models = dm.models()
# Returns: ['request_model', 'query_model', 'response_item']
```

### Explore Model (Statistics + Sample Keys)
```python
report = dm.explore(DataModelType.REQUEST)
# Returns: {
#   'model_type': 'request_model',
#   'total': 42,
#   'by_agent': {'BOCHA': 10, 'XUNFEI': 32},
#   'sample_keys': [key1, key2, ...]
# }
```

### Retrieve Record
```python
data = dm.retrieve(DataModelType.REQUEST, case_key)
# Returns: dict with all model fields
```

### Record Data (with Cascade)
```python
# Record request
request_id = dm.record(DataModelType.REQUEST, {
    'agent_name': 'BOCHA',
    'url': '...',
    'method': 'POST',
    'headers': {...},
    'body': {...},
    'raw_response': {...},
    'http_status': 200,
    'success': True
})

# Record query (linked to request)
request_model = RequestModel(request_id=request_id, agent_name='BOCHA')
query_id = dm.record(DataModelType.QUERY, {
    'agent_name': 'BOCHA',
    'query_keywords': ['AI'],
    'max_results': 10
}, associated_case=request_model)

# Record response items (linked to query)
query_model = QueryModel(query_id=query_id, request_id=request_id)
for item_data in items:
    item_id = dm.record(DataModelType.RESPONSE_ITEM,
        item_data, associated_case=query_model)
```

## Configuration

**File**: `config/data_manager.yaml`

All defaults are defined in YAML - Python code has NO hardcoded defaults.

```yaml
storage:
  backend: "sqlite"
  database:
    path: "data/data_manager.db"
    timeout: 5.0
    check_same_thread: false

models:
  - name: "request_model"
    table: "request_models"
    description: "..."
  - name: "query_model"
    table: "query_models"
    description: "..."
  - name: "response_item"
    table: "response_items"
    description: "..."

cascade:
  request_delete_cascade: true
  query_delete_cascade: true

retention:
  enabled: false

logging:
  level: "INFO"
  log_all_operations: false
```

## Storage

### SQLite Backend
- **Database**: `data/data_manager.db`
- **Tables**: `request_models`, `query_models`, `response_items`
- **Serialization**: JSON for all complex fields
- **Indices**: agent_name, request_id, query_id

### Cascade Deletion
- Delete RequestModel → auto-deletes all QueryModels + ResponseItems
- Delete QueryModel → auto-deletes all ResponseItems
- Configurable in `config/data_manager.yaml`

## Design Principles

✅ **Singleton Pattern** - Single global instance via `get_data_manager()`

✅ **No Hardcoded Defaults** - All config values from YAML only

✅ **Cascade Support** - Automatic cleanup of related records

✅ **JSON Serialization** - Compatible with future agent implementations

✅ **Type Safety** - Dataclass models with validation

✅ **Independent Module** - Zero dependencies on agents or agent_manager

✅ **Performance** - Indexed queries on common fields

## Integration Path

Agents will implement `create_data_value()` methods to fit these models:

```python
# BOCHA agent example
def get_request_data_value(self) -> Dict[str, Any]:
    return {
        'agent_name': self.NAME,
        'url': self.api_endpoint,
        'method': 'POST',
        'headers': self.get_header_dict(),
        'body': self.request_body,
        'raw_response': None,  # Set after API call
        'http_status': 0,      # Set after API call
        'success': True,       # Set after API call
    }

def get_query_data_value(self) -> Dict[str, Any]:
    # Extract common fields from self.request_body
    return {
        'agent_name': self.NAME,
        'query_keywords': [...],  # Parsed from request_body
        'raw_query_body': self.request_body
    }
```

Future scheduler module will orchestrate DataManager + AgentManager together.
