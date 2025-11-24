# Data Manager

Independent data management system for logging API requests and normalized responses.

## Architecture

```
RequestModel (Raw API Log)
    │ cascade delete
    └─→ ResponseItem (Search Result)
```

## Models

| Model | Purpose | Fields |
|-------|---------|--------|
| **RequestModel** | Complete raw API request/response log | request_id, agent_name, url, method, headers, body, raw_response, http_status |
| **ResponseItem** | Single search result (cascade to Request) | item_id, request_id(FK), title, content, source_url, source_name, category, key_entities |

## Public API

```python
from src.data_manager import get_data_manager, DataModelType

dm = get_data_manager()

# List available models
models = dm.models()
# → ['request_model', 'response_item']

# Explore a model (get stats + sample keys)
report = dm.explore(DataModelType.REQUEST)
# → {model_type, total, by_agent, sample_keys}

# Retrieve specific record
data = dm.retrieve(DataModelType.REQUEST, case_key)

# Record data (with cascade associations)
request_id = dm.record(DataModelType.REQUEST, request_dict)
item_id = dm.record(DataModelType.RESPONSE_ITEM, item_dict, associated_case=request_model)
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
```

## Key Features

- **Singleton**: Single global instance via `get_data_manager()`
- **Cascade**: Delete RequestModel → auto-deletes ResponseItems
- **Persistent**: SQLite with auto-created tables and indices
- **JSON-compatible**: All data serialized as JSON (future-proof for new agents)
- **Independent**: No dependencies on agents or agent_manager

## Usage Example

```python
from src.data_manager import get_data_manager, DataModelType, RequestModel

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

# Record response items (linked to request)
request_model = RequestModel(request_id=request_id, agent_name='BOCHA')
for item_data in response_items:
    dm.record(DataModelType.RESPONSE_ITEM, item_data, associated_case=request_model)
```

## Storage

- **Backend**: SQLite (`data/data_manager.db`)
- **Tables**: `request_models`, `response_items`
- **Indices**: On agent_name and request_id for performance
