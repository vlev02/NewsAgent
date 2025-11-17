# NewsAgent Scheduler - Complete Guide

Comprehensive guide to the NewsAgent interactive scheduler system, including settings management, CLI actions, and programmatic usage.

## Quick Navigation

- **New to NewsAgent?** → Start with [SCHEDULER_SETUP.md](../SCHEDULER_SETUP.md)
- **Want to use the interactive CLI?** → Read [SCHEDULER.md](SCHEDULER.md)
- **Need to configure settings?** → See [SCHEDULER_SETTINGS.md](SCHEDULER_SETTINGS.md)
- **Building custom integrations?** → Check the [API Reference](#api-reference) below

## System Overview

The NewsAgent scheduler is a **production-ready, interactive CLI system** for managing the entire news aggregation pipeline. It provides:

```
┌─────────────────────────────────────────────────────────┐
│         NewsAgent Scheduler - Interactive CLI           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Settings Manager                                       │
│  ├─ Load from .env file                               │
│  ├─ Type-safe environment variables                   │
│  ├─ Validate agent configurations                     │
│  └─ Report system status                              │
│                                                        │
│  Interactive Actions                                   │
│  ├─ Explore Recent Research                           │
│  ├─ Submit Query (8-step wizard)                      │
│  ├─ Export Results (JSON/Markdown)                    │
│  ├─ View Statistics                                   │
│  └─ Settings & Configuration                          │
│                                                        │
│  Database Layer                                        │
│  ├─ SQLite3 persistence                               │
│  ├─ Query history tracking                            │
│  ├─ Item deduplication                                │
│  └─ Statistics reporting                              │
│                                                        │
│  Agent Management                                      │
│  ├─ 6 pre-configured agents                           │
│  ├─ Unified query interface                           │
│  ├─ Async-ready architecture                          │
│  └─ Resource tracking                                 │
│                                                        │
└─────────────────────────────────────────────────────────┘
```

## File Organization

```
src/scheduler/
├── __init__.py                    # Module exports
├── scheduler.py                   # Main Scheduler class
├── scheduler_settings.py          # Settings management
├── interactive.py                 # UI utilities
├── config.py                      # Legacy config (deprecated)
└── actions/                       # Action handlers
    ├── __init__.py
    ├── base.py                    # Abstract Action
    ├── explore.py                 # Explore research
    ├── submit_query.py            # Query submission
    ├── export.py                  # Result export
    ├── stats.py                   # Statistics
    └── settings.py                # Configuration view

examples/
├── scheduler.py                   # CLI entry point
├── test_scheduler.py              # Scheduler tests
└── test_scheduler_settings.py     # Settings tests

docs/
├── SCHEDULER.md                   # Interactive use guide
├── SCHEDULER_SETTINGS.md          # Settings reference
└── SCHEDULER_COMPLETE_GUIDE.md    # This file

SCHEDULER_SETUP.md                 # Quick setup guide
```

## Getting Started

### Installation

```bash
# 1. Clone repository (if not already done)
git clone <repository-url>
cd NewsAgent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup environment
cp .env.example .env
nano .env  # Add your API keys
```

### First Run

```bash
# Check configuration
python -m examples.scheduler --show-env

# Run interactive scheduler
python -m examples.scheduler
```

## Core Components

### 1. Scheduler Settings System

**Purpose**: Initialize and manage all configurations from `.env` file

**Key Classes**:
- `EnvironmentVariables`: Type-safe container for env vars
- `SchedulerSettings`: Complete settings manager
- `initialize_scheduler_settings()`: Main entry function

**Usage**:
```python
from src.scheduler.scheduler_settings import initialize_scheduler_settings

settings = initialize_scheduler_settings(env_file=".env")
settings.print_summary()  # Display configuration
```

**Features**:
- Loads from `.env` file automatically
- Validates agent configurations
- Checks database directory
- Supports proxy configuration
- Pretty-print reports

### 2. Interactive Actions

**Purpose**: Provide user-friendly interactive CLI actions

**Available Actions**:
1. **ExploreAction** - Browse research history
2. **SubmitQueryAction** - 8-step query submission
3. **ExportAction** - Export to JSON/Markdown
4. **StatsAction** - View statistics
5. **SettingsAction** - Manage configurations

**Architecture**:
- Abstract `Action` base class
- Dependency injection of db and agents
- Consistent error handling
- Color-coded output

### 3. Interactive UI

**Purpose**: Provide consistent, user-friendly terminal interface

**Features**:
- Color-coded messages (✅ ❌ ⚠️ ℹ️)
- Menu selection with validation
- Text/list input with validation
- Formatted tables
- Progress reporting

**Usage**:
```python
from src.scheduler.interactive import (
    prompt_choice, prompt_text, prompt_list,
    print_success, print_error, print_table
)

choice = prompt_choice(["Option 1", "Option 2"], "Select")
name = prompt_text("Enter name")
items = prompt_list("Enter items (comma-separated)")
```

### 4. Main Scheduler

**Purpose**: Coordinate all components and manage the interactive loop

**Responsibilities**:
- Load settings
- Initialize database
- Setup actions
- Display menu
- Handle user input
- Execute actions

**Usage**:
```python
from src.scheduler import Scheduler
from src.scheduler.scheduler_settings import initialize_scheduler_settings

settings = initialize_scheduler_settings()
scheduler = Scheduler(settings=settings)
scheduler.run()
```

## CLI Usage Examples

### View Configuration

```bash
# Summary view
python -m examples.scheduler --show-env

# Detailed environment variables
python -m examples.scheduler --show-env-vars

# Full initialization report
python -m examples.scheduler
```

### Custom Configuration

```bash
# Use custom .env file
python -m examples.scheduler --env .env.production

# Use custom database
python -m examples.scheduler --db /data/news.db

# Combine options
python -m examples.scheduler --env .env.prod --db /data/prod.db
```

### Run Scheduler

```bash
# Standard run (loads from .env, shows init report, launches CLI)
python -m examples.scheduler

# Only show status
python -m examples.scheduler --show-env
```

## Environment Configuration

### Required Environment Variables

At least one API key from any agent:

```env
# Option 1: BOCHA (recommended for testing)
BOCHA_API_KEY=your_key

# Option 2: XUNFEI
XUNFEI_APPID=your_appid
XUNFEI_APIKey=your_key

# Option 3: Any other agent
HUNYUAN_API_KEY=your_key
QIANFAN_API_KEY=your_key
META_API_KEY=your_key
TWITTER_BEARER_TOKEN=your_token
```

### Optional Configuration

```env
# Database
DATABASE_PATH=newsagent.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=newsagent.log

# Scheduler
DEFAULT_TIME_RANGE=7
DEFAULT_MAX_RESULTS=10
EXPORT_DIRECTORY=data

# Proxy (if needed)
HTTP_PROXY=http://proxy:8080
HTTPS_PROXY=https://proxy:8080
```

## Programmatic Usage

### Basic Usage

```python
from src.scheduler import Scheduler
from src.scheduler.scheduler_settings import initialize_scheduler_settings

# Initialize
settings = initialize_scheduler_settings()

# Create scheduler
scheduler = Scheduler(settings=settings)

# Run interactive loop
scheduler.run()
```

### Advanced Usage

```python
# Access settings components
ready_agents = settings.get_ready_agents()
print(f"Available agents: {list(ready_agents.keys())}")

# Access database
items = scheduler.db.search_items(limit=100)

# Access configuration
db_path = settings.env_vars.database_path
```

### Custom Integration

```python
from src.scheduler import Scheduler
from src.scheduler.actions import ExploreAction

# Create scheduler
scheduler = Scheduler(settings=settings)

# Get specific action
explore_action = scheduler.actions[0]

# Execute action directly
explore_action.execute()
```

## Database Operations

The scheduler uses SQLite3 database with automatic persistence:

```python
# Save query
query_id = scheduler.db.save_query(query)

# Save results
scheduler.db.save_response(response)
scheduler.db.save_items_batch(items)

# Query data
recent = scheduler.db.list_queries(limit=10)
items = scheduler.db.search_items(source_type="BOCHA")

# Statistics
stats = scheduler.db.get_stats()
```

## Query Submission Workflow

The scheduler provides an 8-step guided query submission:

1. **Select Agents** - Choose from XUNFEI, BOCHA, HUNYUAN, QIANFAN, META, TWITTER
2. **Enter Fields** - Specify domains (e.g., "自动驾驶")
3. **Enter Topics** - Specify topics (e.g., "特斯拉FSD")
4. **Select Time** - Choose 1/7/30/365 days
5. **Set Limits** - Result limit per agent
6. **Review** - Confirm all parameters
7. **Preview** - See Jinja2 templates
8. **Execute** - Run query with resource checks

## Export Capabilities

### JSON Export

```json
{
  "export_date": "2024-11-17T14:30:45",
  "item_count": 15,
  "query": {
    "fields": ["自动驾驶"],
    "topics": ["特斯拉FSD"],
    "agents": ["BOCHA"]
  },
  "items": [
    {
      "title": "Article Title",
      "content": "...",
      "source_url": "https://...",
      "source_name": "BOCHA",
      "timestamp": "2024-11-17T12:00:00"
    }
  ]
}
```

### Markdown Export

```markdown
# Search Results Export

**Export Date:** 2024-11-17 14:30:45

## Results (15 items)

### 1. Article Title

**Source:** BOCHA
**URL:** [https://...](https://...)
**Date:** 2024-11-17 12:00

Article content here...
```

## Error Handling

The scheduler provides helpful error messages for common issues:

```
❌ No agents configured!
ℹ️  Please configure API keys in .env file:
   - BOCHA_API_KEY for BOCHA
   - XUNFEI_APPID for XUNFEI
   ...

❌ Database directory not writable
ℹ️  Check write permissions or change DATABASE_PATH

⚠️  XUNFEI: ✗ Missing API Key
```

## Testing

Run the test suite:

```bash
# Test basic functionality
python -m examples.test_imports

# Test scheduler components
python -m examples.test_scheduler

# Test settings management
python -m examples.test_scheduler_settings
```

All components tested and verified:
- ✅ Module imports
- ✅ Settings initialization
- ✅ Agent status checking
- ✅ Database operations
- ✅ UI interactions
- ✅ File I/O operations

## API Reference

### Scheduler Class

```python
class Scheduler:
    def __init__(self, config=None, agents_config=None, settings=None)
    def print_briefing(self) -> None
    def show_main_menu(self) -> Optional[int]
    def run(self) -> None
    def cleanup(self) -> None
```

### SchedulerSettings Class

```python
class SchedulerSettings:
    @classmethod
    def initialize(env_file: str = ".env") -> SchedulerSettings

    def get_ready_agents(self) -> Dict[str, AgentConfig]
    def get_unavailable_agents(self) -> Dict[str, str]
    def validate_critical_config(self) -> bool
    def validate_database_path(self) -> bool
    def print_summary(self) -> None
    def print_env_status(self) -> None
    def full_initialization_report(self) -> bool
    def setup_proxies(self) -> None
    def create_export_directory(self) -> None
```

### Action Classes

```python
class Action(ABC):
    @property
    def name(self) -> str

    @property
    def description(self) -> str

    @abstractmethod
    def execute(self) -> bool
```

### Interactive Utilities

```python
def prompt_choice(options: List[str], prompt_text: str) -> Optional[int]
def prompt_text(prompt_text: str, allow_empty: bool = False) -> Optional[str]
def prompt_list(prompt_text: str, separator: str = ",") -> Optional[List[str]]
def prompt_confirm(prompt_text: str = "Continue") -> bool

def print_header(text: str) -> None
def print_section(text: str) -> None
def print_success(text: str) -> None
def print_error(text: str) -> None
def print_warning(text: str) -> None
def print_info(text: str) -> None
def print_table(headers: List[str], rows: List[List[Any]]) -> None
```

## Troubleshooting

### Common Issues

1. **"No module named 'dotenv'"**
   ```bash
   pip install python-dotenv
   ```

2. **"API key not set" warning**
   - Edit `.env` and add API keys
   - Run `python -m examples.scheduler --show-env-vars` to verify

3. **"Database directory not writable"**
   - Check directory permissions
   - Change `DATABASE_PATH` in `.env`

4. **Environment variables not loading**
   - Verify `.env` file exists
   - Check file syntax (KEY=VALUE, no quotes)
   - Run `python -m examples.scheduler --show-env-vars`

See [SCHEDULER_SETUP.md](../SCHEDULER_SETUP.md) for more troubleshooting.

## Best Practices

1. **Use version control for .env templates**
   - Commit `.env.example` to git
   - Never commit `.env` with real keys

2. **Separate environments**
   - `.env.dev` for development
   - `.env.prod` for production
   - Use `--env` flag to switch

3. **Regular validation**
   - Run `--show-env` before major operations
   - Check agent status in Settings action
   - Monitor logs for configuration issues

4. **Security**
   - Restrict `.env` permissions: `chmod 600 .env`
   - Rotate API keys regularly
   - Don't share keys via email

5. **Documentation**
   - Document required API keys for team
   - Keep setup instructions updated
   - Maintain change log for configuration

## Performance Considerations

- **Database**: Uses SQLite3, suitable for millions of records
- **Memory**: Loads only active configuration into memory
- **I/O**: Settings loaded once at startup
- **UI**: Color output may be slower over slow terminals
- **Network**: Respects agent rate limits

## Security Considerations

- **API Keys**: Stored only in `.env`, never logged
- **Passwords**: Type-safe container prevents accidental exposure
- **File Permissions**: Should restrict `.env` access
- **Proxy Support**: For secure connections through firewalls
- **No Secrets in Code**: All sensitive data from environment

## Future Enhancements

Planned features:
- Configuration encryption
- Hot-reload support
- Async/await execution
- Query scheduling
- Cost tracking
- Custom workflows
- Plugin system

## Support & Documentation

- **Getting Started**: [SCHEDULER_SETUP.md](../SCHEDULER_SETUP.md)
- **Interactive Use**: [SCHEDULER.md](SCHEDULER.md)
- **Settings Reference**: [SCHEDULER_SETTINGS.md](SCHEDULER_SETTINGS.md)
- **Architecture**: [README_NEW_ARCHITECTURE.md](README_NEW_ARCHITECTURE.md)
- **Main README**: [../README.md](../README.md)

## Version History

**v1.0** (November 17, 2024)
- Initial release
- 5 interactive actions
- Complete settings management
- Comprehensive documentation
- Full test coverage

---

**Status**: Production-Ready
**Last Updated**: November 17, 2024
**Maintained By**: Claude Code

For issues or feature requests, see the main project repository.
