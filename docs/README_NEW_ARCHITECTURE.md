# NewsAgent - Agentic AI Searcher Pipeline (Restructured)

A modular, production-ready news aggregation pipeline that integrates multiple AI-powered search APIs into a unified, abstraction-layered architecture.

## 📋 Overview

This restructured version transforms the original notebook-based implementation into a professional pipeline featuring:

- **Modular Agent Architecture**: Abstract base class with concrete implementations for each data source
- **Unified Dataclasses**: `SearchItem`, `QueryRequest`, `QueryResponse`, `AgentConfig` for type safety
- **Pluggable Database**: Support for multiple backends (SQLite3 primary, extensible to PostgreSQL, MongoDB)
- **Jinja2 Templates**: Parametrized prompt templates with consistent parameter naming
- **Multi-Agent Orchestration**: Execute queries in parallel across multiple agents
- **Result Aggregation**: Deduplicate and merge results from different sources
- **Budget Tracking**: Monitor API quota and cost consumption

## 🏗️ Architecture

### Core Components

```
src/
├── dataclasses/              # Data models
│   ├── models.py            # SearchItem, QueryRequest, QueryResponse
│   └── config.py            # AgentConfig (with pre-defined configs)
├── agents/                   # Search agents
│   ├── base.py              # Abstract SearchAgent class
│   └── bocha.py             # BOCHA agent implementation (example)
├── database/                 # Persistence layer
│   ├── backend.py           # Abstract DatabaseBackend
│   ├── sqlite3_backend.py   # SQLite3 implementation
│   └── manager.py           # DatabaseManager facade
├── templates/                # Jinja2 prompt templates
│   ├── xunfei_prompt.jinja2
│   ├── hunyuan_prompt.jinja2
│   └── qianfan_prompt.jinja2
├── pipeline.py              # SearchPipeline orchestrator
└── utils.py                 # Utility functions
```

## 🚀 Quick Start

### Installation

```bash
# Clone repository
cd NewsAgent

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Basic Usage

```python
from src.dataclasses import QueryRequest
from src.dataclasses.config import BOCHA_CONFIG
from src.agents.bocha import BochaAgent
from src.database import SQLite3Backend, DatabaseManager
from src.pipeline import SearchPipeline

# Setup
db = DatabaseManager(SQLite3Backend("newsagent.db"))
db.connect()

bocha_agent = BochaAgent(BOCHA_CONFIG)
pipeline = SearchPipeline({"BOCHA": bocha_agent}, db)

# Create query
query = QueryRequest(
    query_fields=["自动驾驶", "具身智能"],
    query_topics=["特斯拉FSD", "人形机器人"],
    source_agents=["BOCHA"],
    days_back=7,
    max_results=10
)

# Execute
responses = pipeline.execute_query(query)
items = pipeline.aggregate_results(responses)

# Access database
db.print_stats()
db.disconnect()
```

## 📊 Data Models

### SearchItem
Represents a single search result with normalized fields:
```python
@dataclass
class SearchItem:
    id: str
    title: str
    content: str
    source_url: str
    source_name: str
    source_type: str  # XUNFEI, BOCHA, etc
    timestamp: datetime
    # ... optional fields
```

### QueryRequest
Encapsulates search parameters:
```python
@dataclass
class QueryRequest:
    query_id: str
    query_fields: List[str]      # ["自动驾驶", "具身智能"]
    query_topics: List[str]       # ["特斯拉FSD", "人形机器人"]
    source_agents: List[str]      # ["BOCHA", "XUNFEI"]
    days_back: int = 7
    max_results: int = 10
    include_ai_summary: bool = True
    language: str = "zh"
    api_specific_params: Dict = {}
```

### QueryResponse
Result from a single agent:
```python
@dataclass
class QueryResponse:
    response_id: str  # Independent from query_id
    agent_name: str
    query_id: str      # Reference only, not foreign key
    items: List[SearchItem]
    success: bool
    execution_time_ms: int
    tokens_used: Optional[int]
    status: str        # "completed" | "failed" | "rate_limited"
```

## 🔧 Creating Custom Agents

### 1. Define Configuration

```python
from src.dataclasses import AgentConfig

MY_API_CONFIG = AgentConfig(
    agent_name="MY_API",
    agent_type="REST_API",
    api_key="",  # Set via environment
    api_endpoint="https://api.example.com/search",
    supports_time_filter=True,
    time_filter_param_name="date_range",
    default_params={"count": 10}
)
```

### 2. Implement Agent Class

```python
from src.agents.base import SearchAgent

class MyApiAgent(SearchAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.requests_today = 0

    def _load_prompt_template(self) -> Optional[Template]:
        return None  # REST API, no template

    def build_query(self, request: QueryRequest) -> str:
        # Build API-specific query
        pass

    def submit_request(self, query, request) -> QueryResponse:
        # Execute API call
        pass

    def parse_response(self, raw_response) -> List[SearchItem]:
        # Normalize response to SearchItem list
        pass

    def normalize_timestamp(self, timestamp_str) -> datetime:
        # Convert API timestamp to datetime
        pass
```

## 📚 Database Operations

### With Context Manager

```python
with DatabaseManager(SQLite3Backend("newsagent.db")) as db:
    db.save_query(query)
    db.save_response(response)
    results = db.search_items(source_type="BOCHA", limit=50)
```

### Manual Management

```python
db = DatabaseManager(SQLite3Backend())
db.connect()

# Save
db.save_query(query)
db.save_items_batch(items)

# Load
query = db.load_query(query_id)
items = db.search_items(title_contains="AI")

# Aggregate
unique_items = db.deduplicate_items(items, strategy="url")

# Statistics
stats = db.get_stats()
db.print_stats()

# Cleanup
deleted = db.cleanup(days_old=30)

db.disconnect()
```

### Database Schema

The SQLite3 backend creates three main tables:

**queries**: Stores QueryRequest objects
- query_id (PK)
- timestamp, query_fields, query_topics, source_agents
- days_back, time_filter, max_results
- api_specific_params (JSON)

**responses**: Stores QueryResponse objects (NO CASCADE)
- response_id (PK) - Independent from query_id
- agent_name, query_id (text reference)
- items_count, total_estimated
- success, error_message, status
- execution_time_ms, tokens_used

**items**: Stores SearchItem objects (NO CASCADE)
- item_id (PK)
- title, content, source_url, source_name, source_type
- timestamp, category, key_entities, significance
- query_id (text reference), topic_tags

**response_items**: Junction table (NO CASCADE)
- response_id, item_id, position

## 🔗 Parameter Harmonization

The pipeline automatically maps query parameters across different APIs:

### Time Filtering
```python
days_back=7 automatically becomes:
- BOCHA: freshness="oneWeek"
- QIANFAN: search_recency_filter="week"
- XUNFEI: Embedded in prompt as "最近一周"
- TWITTER: start_time=<7 days ago in UTC>
```

### Result Counts
```python
max_results=10 maps to each API's parameter:
- BOCHA: count=10
- QIANFAN: max_completion_tokens=...
- META: size=10
- TWITTER: max_results=10
```

## 📋 Template Variables

All Jinja2 templates accept these standard variables:

```jinja2
{{ query_fields }}           # List[str]
{{ query_topics }}           # List[str]
{{ current_date }}           # YYYY-MM-DD
{{ current_datetime }}       # ISO format
{{ time_description }}       # "最近一周"
{{ language }}               # "zh" or "en"
```

Agent-specific additions in `api_specific_params`:

```python
api_specific_params={
    "XUNFEI": {
        "temperature": 0.3,
        "max_tokens": 4000,
        "search_depth": "deep"
    },
    "QIANFAN": {
        "enable_reasoning": True,
        "resource_types": ["web", "image", "video"]
    }
}
```

## 🎯 Key Features

### 1. No Cascade Relations
- ResponseItems don't cascade to responses or queries
- All relationships stored as text references
- Allows flexible data organization
- Easy to add new relations later

### 2. Independent IDs
- `response_id` ≠ `query_id`
- Both tracked separately in database
- Enable complex query-response matching

### 3. Modular Architecture
- Each agent is independent
- Add new agents without modifying core
- Easy to test individual agents

### 4. Parallel Execution
```python
# Async execution across multiple agents
responses = await pipeline.execute_query_async(query)

# Synchronous execution
responses = pipeline.execute_query(query)
```

### 5. Result Aggregation
```python
# Multiple deduplication strategies
unique_items = pipeline.aggregate_results(
    responses,
    merge_strategy="dedup_by_url"  # or "title", "content_hash"
)
```

## 📊 Statistics & Reporting

```python
# Get database statistics
stats = db.get_stats()
# {
#   'total_queries': 42,
#   'total_responses': 156,
#   'total_items': 1234,
#   'items_by_source': {'BOCHA': 450, 'XUNFEI': 400, ...}
# }

# Generate execution report
report = pipeline.generate_report(query, responses, items)
pipeline.print_report(report)
```

## 🧪 Examples

See `examples/` directory:

- **basic_example.py**: Simple query execution and database access
- More examples coming (parallel execution, custom templates, etc.)

## 📝 Configuration

Agent configurations defined in:
- `src/dataclasses/config.py` - Programmatic configs
- `config/agents.yaml` - YAML-based configurations

## 🔐 Security

- API keys loaded from `.env` (never committed)
- Implement `.env.example` as template
- All secrets in environment variables

## 📈 Next Steps

1. Implement remaining agents (XUNFEI, HUNYUAN, QIANFAN, META, TWITTER)
2. Add async parallel execution
3. Create test suite
4. Add monitoring and logging
5. Document template customization
6. Add PostgreSQL backend
7. Create CLI interface

## 📄 License

[Your License Here]

## 👥 Contributing

[Contributing Guidelines]
