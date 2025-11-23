# Data Manager

Independent data management system for logging API requests, queries, and responses.

## Architecture

```
RequestModel (Raw API Log)
    │ cascade delete
    ├─→ QueryModel (Structured Query)
            │ cascade delete
            └─→ ResponseItem (Search Result)
```

## Models

| Model | Purpose | Fields |
|-------|---------|--------|
| **RequestModel** | Complete raw API request/response log | request_id, agent_name, url, method, headers, body, raw_response, http_status |
| **QueryModel** | Structured query info (cascade to Request) | query_id, request_id(FK), query_keywords, query_topics, days_back, time_filter, max_results |
| **ResponseItem** | Single search result (cascade to Query) | item_id, query_id(FK), title, content, source_url, source_name, category, key_entities |

## Public API

```python
from src.data_manager import get_data_manager, DataModelType

dm = get_data_manager()

# List available models
models = dm.models()
# → ['request_model', 'query_model', 'response_item']

# Explore a model (get stats + sample keys)
report = dm.explore(DataModelType.REQUEST)
# → {model_type, total, by_agent, sample_keys}

# Retrieve specific record
data = dm.retrieve(DataModelType.REQUEST, case_key)

# Record data (with cascade associations)
request_id = dm.record(DataModelType.REQUEST, request_dict)
query_id = dm.record(DataModelType.QUERY, query_dict, associated_case=request_model)
item_id = dm.record(DataModelType.RESPONSE_ITEM, item_dict, associated_case=query_model)
```

## Configuration

**File**: `config/data_manager.yaml`

```yaml
storage:
  backend: sqlite
  database:
    path: data/data_manager.db
    timeout: 5.0
    check_same_thread: false

cascade:
  request_delete_cascade: true
  query_delete_cascade: true
```

## Key Features

- **Singleton**: Single global instance via `get_data_manager()`
- **Cascade**: Delete RequestModel → auto-deletes QueryModels + ResponseItems
- **Persistent**: SQLite with auto-created tables and indices
- **JSON-compatible**: All data serialized as JSON (future-proof for new agents)
- **Independent**: No dependencies on agents or agent_manager

## Usage Example

```python
from src.data_manager import get_data_manager, DataModelType, RequestModel, QueryModel

dm = get_data_manager()

# Record API request
request_id = dm.record(DataModelType.REQUEST, {
    'agent_name': 'BOCHA',
    'url': 'https://api.bochaai.com/v1/web-search',
    'method': 'POST',
    'headers': {...},
    'body': {...},
    'raw_response': {...},
    'http_status': 200
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
for item_data in response_items:
    dm.record(DataModelType.RESPONSE_ITEM, item_data, associated_case=query_model)
```

## Storage

- **Backend**: SQLite (`data/data_manager.db`)
- **Tables**: `request_models`, `query_models`, `response_items`
- **Indices**: On agent_name, request_id, query_id for performance
