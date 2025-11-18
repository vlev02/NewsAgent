# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NewsAgent is a Python-based technical news aggregation pipeline that retrieves and analyzes the latest technology news from multiple AI-powered search and LLM APIs. The project has been restructured from notebook-based implementations into a modular, production-ready architecture with:

- **Agentic abstraction layer** with a unified SearchAgent interface
- **Type-safe dataclasses** for all data models (SearchItem, QueryRequest, QueryResponse)
- **Pluggable database persistence** (SQLite3 with extensibility for other backends)
- **Jinja2 templated prompts** with unified parameter naming across all agents
- **Multi-agent orchestration** for parallel execution and result aggregation
- **No cascade database relations** - responses and items are independent

## Architecture

The restructured codebase follows a modular agent-based design:

### New Modular Structure

```
src/
├── dataclasses/              # Data models (type-safe)
│   ├── models.py            # SearchItem, QueryRequest, QueryResponse
│   └── config.py            # AgentConfig + pre-defined configurations
├── agents/                   # Search agent implementations
│   ├── base.py              # Abstract SearchAgent class
│   └── bocha.py             # BOCHA agent (example implementation)
├── database/                 # Persistence layer (pluggable backends)
│   ├── backend.py           # Abstract DatabaseBackend
│   ├── sqlite3_backend.py   # SQLite3 implementation
│   └── manager.py           # DatabaseManager facade
├── templates/                # Jinja2 prompt templates
│   ├── xunfei_prompt.jinja2
│   ├── hunyuan_prompt.jinja2
│   └── qianfan_prompt.jinja2
├── pipeline.py              # SearchPipeline orchestrator
└── utils.py                 # Utilities (time mapping, JSON parsing)
```

### Legacy Notebooks (Reference)

Original notebook-based implementations are retained for reference:
- **XUNFEI_news_acquisition.ipynb** - Original implementation
- **BOCHA_news_acquisition.ipynb** - Original implementation
- **HUNYUAN_news_acquisition.ipynb** - Original implementation
- **QIANFAN_news_acquisition.ipynb** - Original implementation
- **META_news_acquisition.ipynb** - Original implementation
- **TWITTER_news_acquisition.ipynb** - Original implementation

### New Unified Data Flow

1. **Create QueryRequest** with search parameters and agent list
2. **Initialize agents** from AgentConfig (with credentials from .env)
3. **Execute SearchPipeline** to run queries in parallel across agents
4. **Aggregate results** with deduplication strategies
5. **Save to database** automatically via SearchPipeline
6. **Query database** for historical data and cross-agent analysis

### Configuration

**Single Source of Truth**: `config/agents.yaml`

All agent configurations are now centralized in the YAML file:
- **Agent metadata**: name, type, endpoint

- **Capabilities**: supports_time_filter, supports_ai_summary, needs_json_extraction
- **Default parameters**: model, temperature, count, etc.

The `src/dataclasses/config.py` module loads and parses the YAML file at import time.

API keys are loaded from `.env` file via environment variables.

## Development Commands

### Environment Setup

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies (new architecture)
pip install -r requirements.txt

# The project uses Python 3.12 with these key dependencies:
# - requests: HTTP library for API calls
# - jinja2: Template rendering for prompts
# - python-dotenv: Environment variable management
# - asyncio: Async execution support
```

### Running the New Architecture

```bash
# Run basic example with BOCHA agent
python -m examples.basic_example

# Run with database queries
python -c "from src.database import SQLite3Backend, DatabaseManager; \
db = DatabaseManager(SQLite3Backend()); db.connect(); db.print_stats(); db.disconnect()"

# Interactive Python shell to test pipeline
python -i examples/basic_example.py
```

### Running Legacy Notebooks (Reference)

```bash
# For original notebook-based implementations
jupyter lab

# Then open any *.ipynb file in the root directory
```

### Environment Configuration

**Single Entry Point Pattern:**

NewsAgent uses a unified environment loading system with a single entry point:

```python
from src.scheduler.scheduler_settings import SchedulerSettings

# Load from .env
settings = SchedulerSettings.initialize()

# Load with overrides (for testing)
settings = SchedulerSettings.initialize(
    database_path="data/test.db",
    log_level="DEBUG",
    bocha_api_key="override-key"
)
```

**Setup .env file:**

```bash
# Copy .env.example to .env and fill in your API credentials
cp .env.example .env

# Edit .env with your API keys for:
# - XUNFEI (Spark API)
# - HUNYUAN (Tencent)
# - QIANFAN (Baidu)
# - BOCHA (Web Search)
# - META (MetaSo Search)
# - TWITTER (Twitter/X API)

# Never commit .env to version control (already in .gitignore)
```

**Testing without modifying .env:**

```python
# Override specific values for testing
settings = SchedulerSettings.initialize(
    database_path="data/demo.db",  # Use test database
    log_level="DEBUG"               # Inherit rest from .env
)

# Configure debug flags
from src.debug_config import DebugConfig
DebugConfig.fake_response_enabled = True
DebugConfig.fake_response_update = True
```

See `examples/demo_fake_response.py` for a complete demonstration and `docs/ENVIRONMENT_OVERRIDE_QUICK_REFERENCE.md` for the complete guide.

## Key Implementation Patterns

### Agent Architecture

All agents inherit from `SearchAgent` abstract base class:

```python
class MyAgent(SearchAgent):
    def build_query(self, request: QueryRequest) -> Union[str, Dict]:
        """Build API-specific query"""
        pass

    def submit_request(self, query, request: QueryRequest) -> QueryResponse:
        """Execute API call"""
        pass

    def parse_response(self, raw_response) -> List[SearchItem]:
        """Normalize response to SearchItem list"""
        pass
```

### Dataclass Models

**SearchItem**: Normalized result from any agent
```python
@dataclass
class SearchItem:
    id: str                          # UUID
    title: str
    content: str
    source_url: str
    source_name: str
    source_type: str                # "BOCHA", "XUNFEI", etc
    timestamp: datetime
    metadata: Dict[str, Any]        # Source-specific fields
```

**QueryRequest**: Unified query across all agents
```python
@dataclass
class QueryRequest:
    query_id: str
    query_fields: List[str]         # ["自动驾驶", "具身智能"]
    query_topics: List[str]         # ["特斯拉FSD", "人形机器人"]
    source_agents: List[str]        # ["BOCHA", "XUNFEI"]
    days_back: int = 7
    api_specific_params: Dict = {}  # {"XUNFEI": {"temperature": 0.3}}
```

**QueryResponse**: Result from one agent (NO CASCADE to QueryRequest)
```python
@dataclass
class QueryResponse:
    response_id: str                # Independent UUID
    agent_name: str
    query_id: str                   # Text reference only
    items: List[SearchItem]
    success: bool
    status: str                     # "completed", "failed", "quota_exceeded"
```

### Database Design

**No cascade relations**:
- `responses` table has `query_id` as TEXT (not foreign key)
- `items` table has `query_id` as TEXT (not foreign key)
- `response_items` junction table (no cascade)
- Each table can be independently queried and modified

Benefits:
- Flexible data organization
- No orphaned records from deletions
- Easy to add new relations
- Support complex analytical queries

### Jinja2 Template Parameters

All templates receive unified parameters:
```jinja2
{{ query_fields }}           # List of domains
{{ query_topics }}           # List of topics
{{ current_date }}           # YYYY-MM-DD
{{ time_description }}       # "最近一周"
{{ language }}               # "zh" or "en"
```

### Time Filtering Harmonization

Unified `days_back` parameter maps to API-specific formats:
```python
days_back=7 automatically becomes:
- BOCHA: freshness="oneWeek"
- QIANFAN: search_recency_filter="week"
- XUNFEI: Embedded in prompt as "最近一周"
- TWITTER: start_time parameter calculation
```

## Important Implementation Details

### Error Handling Patterns

Comprehensive error handling in `submit_and_parse()`:
1. Exception catching with detailed messages
2. Status codes: "completed", "failed", "quota_exceeded"
3. Error messages stored in `QueryResponse.error_message`

### JSON Response Extraction

For LLM-based agents (XUNFEI, HUNYUAN, QIANFAN):
- Handles both markdown code blocks: ` ```json { ... } ``` `
- Direct JSON: ` { ... } `
- Full response parsing with graceful fallback
- Implemented in `src/utils.normalize_json_response()`

## Database Operations

### Key Methods

```python
# Database Manager
db = DatabaseManager(SQLite3Backend("newsagent.db"))
db.connect()

# Save operations
db.save_query(query)
db.save_response(response)
db.save_items_batch(items)

# Load operations
query = db.load_query(query_id)
items = db.search_items(source_type="BOCHA", limit=50)
responses = db.list_responses(agent_name="XUNFEI")

# Deduplication
unique_items = db.deduplicate_items(items, strategy="url")  # or "title", "content_hash"

# Statistics
stats = db.get_stats()
db.print_stats()

# Cleanup
deleted = db.cleanup(days_old=30)

db.disconnect()
```

### Context Manager Usage

```python
with DatabaseManager(SQLite3Backend("newsagent.db")) as db:
    db.save_query(query)
    db.save_response(response)
    results = db.search_items(source_type="BOCHA")
# Database auto-disconnects here
```

## File Organization

```
NewsAgent/
├── src/                          # New modular architecture
│   ├── dataclasses/
│   ├── agents/
│   ├── database/
│   ├── templates/
│   ├── pipeline.py
│   └── utils.py
├── config/                       # Configuration files
│   └── agents.yaml
├── examples/                     # Usage examples
│   └── basic_example.py
├── .env.example                  # Environment template
├── .gitignore
├── CLAUDE.md
├── README_NEW_ARCHITECTURE.md    # New architecture docs
├── requirements.txt
│
├── XUNFEI_http_demo.py           # Legacy reference
├── XUNFEI_news.py
├── *_acquisition.ipynb           # Legacy notebooks (reference)
└── tech_news_*.json              # Output data files
```

The `.gitignore` excludes:
- `.venv/` - Virtual environment
- `.env` - API credentials
- `*.log`, `*.out` - Log files
- `__pycache__/` - Python cache
- `*.json` - Generated news data files
- `newsagent.db` - Database file (optional)

## Architecture Highlights

### 1. Modular Design
- Each agent is independent and testable
- Abstract base class ensures consistency
- Easy to add new agents without modifying core

### 2. Type Safety
- All data models are dataclasses
- IDE autocomplete and type checking
- Clear contracts between components

### 3. Pluggable Database
- Abstract DatabaseBackend interface
- SQLite3 primary implementation
- Extensible to PostgreSQL, MongoDB, etc
- No cascade relations for flexibility

### 4. Unified Parameters
- Single QueryRequest for all agents
- Automatic parameter mapping per API
- Jinja2 template standardization
- Consistent timestamp handling

### 5. Multi-Agent Orchestration
- Execute multiple agents in parallel
- Automatic result aggregation
- Deduplication strategies
- Comprehensive execution reports

## Critical Development Guidelines

### Documentation Policy
**DO NOT** output any summary/reference documentation files (*.md) without explicit permission. Documentation files are not helpful and create clutter in the project. Only create documentation when explicitly requested by the user.

### Git Commit Policy
**DO NOT** submit any git commits without explicit permission. Wait for user approval before creating commits. User will explicitly request commits when ready.

### Testing Policy
- All test modules **MUST** be saved in the `tests/` directory
- All tests **MUST** follow unittest format (inherit from `unittest.TestCase`)
- Test file naming: `tests/test_*.py` (e.g., `tests/test_agents.py`, `tests/test_database.py`)
- Example structure:
  ```python
  import unittest
  from src.agents.bocha import BochaAgent

  class TestBochaAgent(unittest.TestCase):
      def setUp(self):
          """Set up test fixtures"""
          pass

      def test_agent_initialization(self):
          """Test agent can be initialized"""
          self.assertIsNotNone(agent)

      def tearDown(self):
          """Clean up after tests"""
          pass
  ```

## Next Steps for Development

1. **Implement remaining agents**: XUNFEI, HUNYUAN, QIANFAN, META, TWITTER
2. **Add async execution**: Full async/await support in SearchPipeline
3. **Create test suite**: Unit and integration tests for all components (in `tests/` with unittest format)
4. **Add logging**: Comprehensive logging for debugging and monitoring
5. **Implement CLI**: Command-line interface for common operations
6. **PostgreSQL backend**: Alternative database implementation
7. **Configuration management**: Load from YAML/JSON files
8. **Monitoring**: Track API costs, execution times, error rates

## Git Commit History

Recent commits follow a feature-based naming convention:
- `feat(API): New API integration` - Adding new data source
- `feat(agents): Update integration` - Improving existing integrations
- `refactor: Restructure to modular architecture` - Latest restructuring

The project has transitioned from notebook-based to production-ready code.
