# NewsAgent - Agentic AI News Aggregation Pipeline

A professional, modular news aggregation pipeline that integrates multiple AI-powered search APIs into a unified, production-ready system.

## 📋 Quick Overview

NewsAgent has been restructured from notebook-based implementations into a modern, type-safe, agentic architecture supporting:

- **6 Data Sources**: XUNFEI, BOCHA, HUNYUAN, QIANFAN, META, TWITTER
- **Modular Agents**: Abstract SearchAgent with independent implementations
- **Type-Safe Data**: Dataclasses for SearchItem, QueryRequest, QueryResponse
- **Pluggable Database**: SQLite3 (extensible to PostgreSQL, MongoDB)
- **Parameter Harmonization**: Unified interface across diverse APIs
- **Multi-Agent Orchestration**: Execute agents in parallel with result aggregation

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup environment
cp .env.example .env
# Edit .env with your API keys

# 3a. Run the interactive scheduler
python -m examples.scheduler

# 3b. Or run the basic example
python -m examples.basic_example
```

## 📁 Directory Structure

```
NewsAgent/
├── src/                          # Production code (new modular architecture)
│   ├── dataclasses/             # Type-safe data models
│   ├── agents/                  # Search agent implementations
│   ├── database/                # Pluggable persistence layer
│   ├── scheduler/               # Interactive terminal-based CLI
│   ├── templates/               # Jinja2 prompt templates
│   ├── pipeline.py              # Multi-agent orchestrator
│   └── utils.py                 # Utility functions
│
├── config/                       # Configuration files
│   └── agents.yaml              # Agent capabilities & defaults
│
├── examples/                     # Usage examples
│   ├── scheduler.py             # Interactive terminal-based CLI
│   ├── basic_example.py         # Complete working example
│   └── test_scheduler.py        # Scheduler component tests
│
├── docs/                         # Documentation
│   ├── CLAUDE.md                # Development guidance
│   ├── README_NEW_ARCHITECTURE.md
│   └── IMPLEMENTATION_SUMMARY.md
│
├── legacy/                       # Original notebook implementations (reference)
│   ├── *_acquisition.ipynb      # Original notebooks
│   ├── XUNFEI_http_demo.py
│   └── XUNFEI_news.py
│
├── data/                         # Output data files
│   └── tech_news_*.json         # Generated search results
│
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## 📚 Documentation

- **[docs/SCHEDULER.md](docs/SCHEDULER.md)** - Complete guide to the interactive scheduler
- **[docs/CLAUDE.md](docs/CLAUDE.md)** - Development guidance for Claude Code
- **[docs/README_NEW_ARCHITECTURE.md](docs/README_NEW_ARCHITECTURE.md)** - Complete architecture guide
- **[docs/IMPLEMENTATION_SUMMARY.md](docs/IMPLEMENTATION_SUMMARY.md)** - Technical details

## 🏗️ Architecture

### Core Components

**Dataclasses** (Type-Safe Models)
- `SearchItem` - Normalized search results
- `QueryRequest` - Unified query interface
- `QueryResponse` - Independent response objects (no cascade)
- `AgentConfig` - Agent configuration with pre-defined setups

**Agents** (Unified Interface)
- Abstract `SearchAgent` base class
- `BochaAgent` - Complete implementation example
- Other agents follow the same pattern

**Database** (Pluggable Persistence)
- Abstract `DatabaseBackend` interface
- `SQLite3Backend` - Full implementation (4 tables, 4 indices)
- `DatabaseManager` - Facade with context manager support

**Pipeline** (Multi-Agent Orchestration)
- `SearchPipeline` - Coordinate multiple agents
- Automatic result aggregation and deduplication
- Comprehensive execution reporting

### Key Design Principles

✅ **Modular** - Each agent is independent and testable
✅ **Type-Safe** - Full dataclass coverage with IDE support
✅ **Unified** - Single interface for 6 different APIs
✅ **Flexible** - No cascade database relations
✅ **Production-Ready** - Error handling, budget tracking, rate limiting
✅ **Documented** - Comprehensive guides and docstrings

## 🎯 Interactive Scheduler

The easiest way to use NewsAgent is through the interactive **Scheduler CLI**:

```bash
python -m examples.scheduler
```

This launches a terminal-based interface with:
1. **Explore Recent Research** - Browse queries, responses, and search results
2. **Submit Query** - 8-step guided query submission with validation
3. **Export Results** - Save to JSON or Markdown format
4. **View Statistics** - Database overview and project metrics
5. **Settings** - Agent configuration and capabilities

See [docs/SCHEDULER.md](docs/SCHEDULER.md) for complete guide.

## 🔄 Programmatic Workflow

For custom scripts, use the Python API directly:

```python
from src.dataclasses import QueryRequest
from src.dataclasses.config import BOCHA_CONFIG
from src.agents.bocha import BochaAgent
from src.database import SQLite3Backend, DatabaseManager
from src.pipeline import SearchPipeline

# Setup database
with DatabaseManager(SQLite3Backend("newsagent.db")) as db:
    # Initialize agent
    agent = BochaAgent(BOCHA_CONFIG)

    # Create pipeline
    pipeline = SearchPipeline({"BOCHA": agent}, db)

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

    # Report
    report = pipeline.generate_report(query, responses, items)
    pipeline.print_report(report)
```

## 📊 Data Models

### SearchItem
Normalized search result from any agent with fields:
- `id, title, content, source_url, source_name, source_type, timestamp`
- Optional: `category, key_entities, relevance_score, significance, metadata`

### QueryRequest
Unified query interface:
- `query_fields` - Domains (e.g., "自动驾驶", "具身智能")
- `query_topics` - Specific topics
- `source_agents` - Which agents to use
- `days_back` - Time filter (1, 7, 30, 365)
- `api_specific_params` - API-specific overrides

### QueryResponse
Result from single agent (independent ID):
- `response_id` - Different from `query_id` (no cascade)
- `items` - List of SearchItem results
- `status` - "completed", "failed", "quota_exceeded"
- `execution_time_ms, tokens_used, budget_consumed`

## 🗄️ Database

### Tables (No Cascade Relations)
- **queries** - QueryRequest storage
- **responses** - QueryResponse storage (query_id as TEXT)
- **items** - SearchItem storage (query_id as TEXT)
- **response_items** - Junction table

### Methods
```python
db.save_query(query)
db.save_response(response)
db.search_items(source_type="BOCHA", limit=50)
db.deduplicate_items(items, strategy="url")
db.get_stats()
db.cleanup(days_old=30)
```

## ⚙️ Configuration

### Agents (Pre-defined)
- XUNFEI (LLM-based web search)
- BOCHA (REST API web search)
- HUNYUAN (Tencent API)
- QIANFAN (Baidu AppBuilder)
- META (MetaSo search)
- TWITTER (Social media API)

Each with:
- Endpoint, auth method
- Rate limits, quota
- Capabilities (time filter, AI summary, streaming)
- Default parameters

### Environment Variables
```bash
XUNFEI_APPID=...
XUNFEI_APISecret=...
BOCHA_API_KEY=...
HUNYUAN_API_KEY=...
QIANFAN_API_KEY=...
META_API_KEY=...
TWITTER_BEARER_TOKEN=...
```

## 📈 Next Steps

- [ ] Implement remaining agents (XUNFEI, HUNYUAN, QIANFAN, META, TWITTER)
- [ ] Add async/await execution support
- [ ] Create comprehensive test suite
- [ ] Add logging infrastructure
- [ ] Implement CLI interface
- [ ] Add PostgreSQL backend
- [ ] API cost monitoring

## 📝 Legacy Reference

Original notebook-based implementations are in `legacy/`:
- `*_acquisition.ipynb` - Original notebooks
- `XUNFEI_http_demo.py` - Interactive demo
- `XUNFEI_news.py` - Structured extraction

These are retained for reference but the new architecture in `src/` is the recommended approach.

## 📂 Output Data

Generated search results are stored in `data/`:
- Format: `tech_news_{source}_{timestamp}.json`
- Example: `tech_news_bocha_websearch_20251110_143535.json`

## 🔧 Development

### Common Commands

```bash
# Run basic example
python -m examples.basic_example

# Check database
python -c "from src.database import *; db = DatabaseManager(SQLite3Backend()); \
db.connect(); db.print_stats(); db.disconnect()"

# View documentation
cat docs/CLAUDE.md
cat docs/README_NEW_ARCHITECTURE.md

# Run legacy notebooks
jupyter lab
# Open *_acquisition.ipynb files
```

### Key Files to Review

1. **src/agents/bocha.py** - Example agent implementation
2. **src/database/sqlite3_backend.py** - Database implementation
3. **examples/basic_example.py** - Complete usage example
4. **docs/CLAUDE.md** - Development guidance

## 📄 Files

### Root Level (Essential)
- `.env.example` - Environment template
- `.gitignore` - Git ignore rules
- `requirements.txt` - Dependencies
- `README.md` - This file

### Documentation (docs/)
- `CLAUDE.md` - Claude Code development guidance
- `README_NEW_ARCHITECTURE.md` - Architecture guide
- `IMPLEMENTATION_SUMMARY.md` - Technical summary

### Production Code (src/)
- `dataclasses/` - Type-safe models
- `agents/` - Agent implementations
- `database/` - Database layer
- `templates/` - Jinja2 templates
- `pipeline.py` - Orchestrator
- `utils.py` - Utilities

### Configuration (config/)
- `agents.yaml` - Agent configuration

### Examples (examples/)
- `basic_example.py` - Working example

### Legacy (legacy/)
- `*_acquisition.ipynb` - Original notebooks
- `XUNFEI_*.py` - Original scripts

### Data (data/)
- `tech_news_*.json` - Generated results

## 🎯 Status

✅ **Complete**: Architecture and foundation
- Dataclasses
- Database layer (SQLite3)
- Agent framework (abstract + BOCHA example)
- Pipeline orchestrator
- Documentation

📋 **To Do**: Implementation and features
- [ ] Remaining agents
- [ ] Async execution
- [ ] Tests
- [ ] CLI
- [ ] PostgreSQL backend

## 📞 Support

- Check **docs/CLAUDE.md** for development guidance
- Review **docs/README_NEW_ARCHITECTURE.md** for architecture details
- See **examples/basic_example.py** for usage examples

---

**Version**: 2.0 (Restructured)
**Status**: Production-Ready Foundation
**Last Updated**: November 17, 2025
