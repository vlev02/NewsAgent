# Data Manager Explorer - Interactive Guide

## Overview

`call_data_explorer.py` is an interactive script that guides users to explore data items saved and managed by DataManager. It provides a comprehensive interface to browse, search, and analyze data across the three data models: RequestModel, QueryModel, and ResponseItem.

## Quick Start

```bash
python scripts/call_data_explorer.py
```

The script will launch an interactive menu-driven interface where you can navigate through various exploration options.

## Features

### 1. 📊 Overview Statistics
Display comprehensive statistics across all data models:
- Total record counts for each model type
- Breakdown by agent name
- Quick insights into data distribution

```
Total Records:
  • request_model        :    158 records
  • query_model          :     96 records
  • response_item        :    105 records
```

### 2. 🕐 Latest Items
View the most recently created items for each model type:
- Configurable limit (1-50 items per model)
- Display key information for quick scanning
- Sample data preview with timestamps

**Example Output:**
```
[1] REQUEST 3216d8ad...
    Agent: BOCHA
    Status: 200
    Time: 2024-11-22
    Execution: 1500ms
```

### 3. 🔗 Cascade Explorer
Explore relationships between data models interactively:
- **REQUEST → QUERY → RESPONSE_ITEM** cascade chain
- Start from either REQUEST or QUERY
- Interactive navigation through relationships
- View associated items at each level

**Workflow:**
1. Select starting model (REQUEST or QUERY)
2. View or input case ID
3. See all associated items at the next level
4. Optionally cascade deeper

### 4. 🔍 Search by Agent
Filter and view data by agent name:
- List all available agents in the database
- View statistics per agent
- Understand which agents have contributed data

**Available Agents Example:**
```
1. BOCHA
2. META
3. XUNFEI
4. DEMO_AGENT
```

### 5. 🔍 Search by Case ID
Find and inspect specific records:
- Search across all model types
- Display full record details
- Interactive cascade exploration from found records

**Search Flow:**
1. Enter case ID (REQUEST, QUERY, or RESPONSE_ITEM ID)
2. System searches all models
3. If found, displays complete record information
4. Optionally cascade to related records

### 6. 💾 Export Data to JSON
Export data to JSON files for external analysis:
- **Statistics summary** - High-level counts
- **All REQUEST records** - All API requests
- **All QUERY records** - All search queries
- **All RESPONSE_ITEM records** - All results
- **Full export** - Complete data dump

**Export Examples:**
```
datamanager_stats.json       # Statistics only
datamanager_requests.json    # All requests
datamanager_queries.json     # All queries
datamanager_items.json       # All response items
datamanager_full.json        # Complete export
```

## Interactive Menu Structure

```
📚 DataManager Explorer
│
├── 1. View Overview Statistics
│   └── Display total counts and agent breakdown
│
├── 2. View Latest Items
│   ├── Choose limit (1-50)
│   └── Display latest items per model
│
├── 3. Explore Cascade Relationships
│   ├── Start from REQUEST
│   │   └── View associated QUERYs
│   │       └── View associated RESPONSE_ITEMs
│   │
│   └── Start from QUERY
│       └── View associated RESPONSE_ITEMs
│
├── 4. Search by Agent
│   ├── Select agent from list
│   └── View statistics for that agent
│
├── 5. Search by Case ID
│   ├── Enter case ID
│   ├── View full record details
│   └── Cascade to related records
│
├── 6. Export Data to JSON
│   ├── Choose export type
│   └── Save to file
│
└── 7. Exit
```

## Data Model Overview

### RequestModel
Captures complete API requests and responses:
- `request_id` - Unique identifier
- `agent_name` - Which agent made the request
- `url` - API endpoint
- `method` - HTTP method (usually POST)
- `http_status` - Response status code
- `execution_time_ms` - Time taken
- `success` - Whether request succeeded
- `raw_response` - Complete API response

### QueryModel
Normalizes query/search parameters:
- `query_id` - Unique identifier
- `request_id` - Associated REQUEST (foreign key)
- `agent_name` - Query agent
- `query_keywords` - Search keywords
- `query_topics` - Subject topics
- `max_results` - Result limit
- `language` - Language code
- `raw_query_body` - Original API request body

### ResponseItem
Individual search results:
- `item_id` - Unique identifier
- `query_id` - Associated QUERY (foreign key)
- `agent_name` - Source agent
- `title` - Result title
- `content` - Result content
- `source_url` - Original URL
- `source_name` - Source name
- `relevance_score` - Relevance (0-1)
- `key_entities` - Extracted entities

## Cascade Relationships

The data follows a strict cascade chain:

```
REQUEST (1)
    ↓
    └─→ QUERY (N)
            ↓
            └─→ RESPONSE_ITEM (M)
```

### Understanding Cascade:
- One REQUEST can have multiple QUERYs
- One QUERY can have multiple RESPONSE_ITEMs
- RESPONSE_ITEM is a leaf node (no further cascade)
- Deleting REQUEST cascades to QUERY and RESPONSE_ITEM

## Smart Query Format

The explorer uses DataManager's `smart_query()` method internally:

```python
# Get statistics
dm.smart_query()  # Returns: {'request_model': 158, 'query_model': 96, ...}

# Get latest N items
dm.smart_query({'request_model': 5, 'query_model': 3})

# Cascade: REQUEST → QUERY
dm.smart_query({'request_model': 'uuid-string'})  # Returns associated QUERYs

# Cascade: QUERY → RESPONSE_ITEM
dm.smart_query({'query_model': 'uuid-string'})  # Returns associated items
```

## Example Workflows

### Workflow 1: Understand Data Distribution
1. Select **View Overview Statistics**
2. Review total counts and agent breakdown
3. Identify which agents have the most data

### Workflow 2: Find Recent Activity
1. Select **View Latest Items**
2. Set limit to 10
3. Review most recent requests, queries, and results

### Workflow 3: Explore Specific Agent
1. Select **Search by Agent**
2. Choose agent from list
3. View statistics for that agent

### Workflow 4: Trace a Query
1. Select **Explore Cascade Relationships**
2. Select to start from REQUEST
3. Enter REQUEST ID
4. View associated QUERYs
5. Choose a QUERY to explore
6. View associated RESPONSE_ITEMs
7. Examine specific results

### Workflow 5: Find Specific Record
1. Select **Search by Case ID**
2. Enter known case ID
3. System finds and displays record
4. Optionally cascade to related records

### Workflow 6: Export for Analysis
1. Select **Export Data to JSON**
2. Choose export type (e.g., "All QUERY records")
3. Data saved to `datamanager_queries.json`
4. Use with external tools for analysis

## Display Formats

### Overview Display
```
📊 DataManager Overview

Total Records:
  • request_model        :    158 records
  • query_model          :     96 records
  • response_item        :    105 records

  Total                :    359 records

Breakdown by Model:

  request_model:
    - BOCHA                :  103 records
    - META                 :   19 records
```

### Item Display (List View)
```
[1] REQUEST 3216d8ad...
    Agent: BOCHA
    Status: 200
    Time: 2024-11-22
    Execution: 1500ms

[2] QUERY 9b11135d...
    Agent: BOCHA
    Keywords: ['AI', 'news']
    Max results: 10
    Time: 2024-11-22
```

### Cascade Navigation
```
✓ Found 2 associated query(ies)

[1] QUERY 96d78672...
    Agent: DEMO_AGENT
    Keywords: ['AI', 'news']
    Max results: 10
    Time: 2024-11-22

Explore RESPONSE_ITEMs for query 1? (y/n):
```

## Error Handling

The script provides helpful error messages:

```
❌ Case ID 'invalid-id' not found in any model

❌ Error: REQUEST ID 'nonexistent' not found
```

## Performance Considerations

- **Large datasets**: Use "Latest Items" with a reasonable limit (1-50)
- **Export**: Limit to 1000 items per model for large datasets
- **Search**: By ID is fast; by agent requires indexing

## File Outputs

When exporting data, files are saved to the project root:

```
NewsAgent/
├── datamanager_stats.json       # Size: < 1 KB
├── datamanager_requests.json    # Size: varies
├── datamanager_queries.json     # Size: varies
├── datamanager_items.json       # Size: varies
└── datamanager_full.json        # Size: could be large
```

## Integration with DataManager

The explorer is built on top of DataManager's public API:

```python
from src.data_manager import get_data_manager, DataModelType

dm = get_data_manager()

# Available methods:
dm.record(model_type, data_value, associated_case=None)
dm.retrieve(model_type, case_key)
dm.explore(model_type)
dm.models()
dm.smart_query(query_arg)
```

## Troubleshooting

### No data appears
- Ensure `scripts/call_agent.py` has been run to populate data
- Check that DataManager database file exists

### Export fails
- Ensure write permissions in project root
- Check available disk space
- Verify no file lock conflicts

### Cascade shows no results
- Verify case ID is correct
- Check that associated records exist
- Note: RESPONSE_ITEM has no cascade (leaf node)

## Advanced Usage

### Accessing raw DataManager
The explorer provides access to the underlying DataManager instance:

```python
explorer = DataExplorer()
dm = explorer.dm  # Direct access to DataManager singleton

# Use DataManager directly
result = dm.smart_query({'request_model': 100})
item = dm.retrieve(DataModelType.REQUEST, 'uuid-string')
```

### Custom filtering
While the explorer doesn't support complex filtering, you can modify the script to add custom logic for specific analysis needs.

## See Also

- [DataManager API Documentation](../src/data_manager/README.md)
- [call_agent.py](call_agent.py) - Record new data
- [test_data_manager.py](../tests/test_data_manager.py) - Unit tests with examples
