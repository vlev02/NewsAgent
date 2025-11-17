# Module Checking Guide - NewsAgent Project

A comprehensive guide for understanding and verifying the NewsAgent architecture module by module. This guide will help you systematically review the entire codebase and ensure all components work correctly together.

**Total Modules**: 29 | **Phases**: 6 | **Estimated Time**: 2-3 hours for complete review

---

## Table of Contents

1. [Quick Navigation](#quick-navigation)
2. [Architecture Overview](#architecture-overview)
3. [Phase-by-Phase Checking](#phase-by-phase-checking)
4. [Dependency Graph](#dependency-graph)
5. [Known Issues & Missing Components](#known-issues--missing-components)
6. [Verification Checklist](#verification-checklist)

---

## Quick Navigation

| Phase | Name | Modules | Dependencies | Est. Time |
|-------|------|---------|--------------|-----------|
| 1 | **Foundation & Config** | 5 modules | None | 20 min |
| 2 | **Utilities & Helpers** | 4 modules | Foundation | 25 min |
| 3 | **Data Models** | 3 modules | Foundation | 20 min |
| 4 | **Database Layer** | 3 modules | Foundation + Utils | 25 min |
| 5 | **Agent System** | 6 modules | All previous | 40 min |
| 6 | **Orchestration & CLI** | 8 modules | All previous | 40 min |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 6: ORCHESTRATION                       │
│  (Scheduler, CLI, Examples, Interactive UI, Pipeline)           │
└─────────────────────────────────────────────────────────────────┘
                              ↑ depends on
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 5: AGENT SYSTEM                         │
│  (Base Agent, BochaAgent, Template Engine, Config Manager)      │
└─────────────────────────────────────────────────────────────────┘
                              ↑ depends on
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 4: DATABASE LAYER                       │
│  (Database Manager, SQLite Backend, Models)                      │
└─────────────────────────────────────────────────────────────────┘
                              ↑ depends on
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 3: DATA MODELS                          │
│  (SearchItem, QueryRequest, QueryResponse)                       │
└─────────────────────────────────────────────────────────────────┘
                              ↑ depends on
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 2: UTILITIES                            │
│  (FakeResponseManager, DebugLogger, Debug Config)               │
└─────────────────────────────────────────────────────────────────┘
                              ↑ depends on
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1: FOUNDATION                           │
│  (Config files, Environment setup, Enums, Utils)                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase-by-Phase Checking

### PHASE 1: Foundation & Config (5 modules)

These modules establish the project foundation and should be checked first.

#### Module 1.1: Environment Configuration
- **File**: `config/.env.example`
- **Purpose**: Template for environment variables with all API keys and settings
- **Type**: Configuration template
- **What to Check**:
  - All 6 agent API keys defined (BOCHA, XUNFEI, HUNYUAN, QIANFAN, META, TWITTER)
  - Database path configured
  - Export directory defined
  - All comments are clear and helpful
- **Key Variables**:
  - `BOCHA_API_KEY`, `BOCHA_API_TOKEN`
  - `XUNFEI_*` (multiple env vars)
  - `HUNYUAN_*` (multiple env vars)
  - `QIANFAN_*` (multiple env vars)
  - Database path: `APP_DATABASE_PATH`
  - Export path: `APP_EXPORT_PATH`
- **Verification**:
  - [ ] File exists at `/config/.env.example`
  - [ ] All agent API key placeholders present
  - [ ] Comments explain purpose of each variable
  - [ ] Example values are sensible (not actual keys)

---

#### Module 1.2: Core Enums
- **File**: `src/enums.py`
- **Purpose**: Enumeration classes for time filters, result types, etc.
- **Key Enums**: `TimeFilter`, `ResultType`, `SourceType`, `AgentType`
- **What to Check**:
  - TimeFilter values (LAST_DAY, LAST_WEEK, LAST_MONTH, LAST_3MONTHS, LAST_YEAR, ALL_TIME)
  - Proper enum structure and inheritance
  - String representation methods working
- **Dependencies**: None (pure enum definitions)
- **Verification**:
  - [ ] All TimeFilter enum values defined
  - [ ] Enums have proper `__str__()` or `__repr__()` methods
  - [ ] No circular dependencies with other modules
  - [ ] Test: `from src.enums import TimeFilter` works

---

#### Module 1.3: Utilities (Original)
- **File**: `src/utils.py`
- **Purpose**: Time filter mapping, API utility functions, constants
- **Key Functions**:
  - `get_api_time_filter()` - converts TimeFilter enum to API-specific format
  - `TIME_FILTER_MAPPING` - dictionary mapping TimeFilter to different API formats
- **Important Note**: This is the original utils.py module (not the utils/ package)
- **What to Check**:
  - TIME_FILTER_MAPPING contains mappings for all agents
  - `get_api_time_filter()` function handles all TimeFilter enums
  - Proper handling of edge cases (None values, unknown filters)
- **Dependencies**: `src.enums`
- **Verification**:
  - [ ] `from src.utils import TIME_FILTER_MAPPING` works
  - [ ] `from src.utils import get_api_time_filter` works
  - [ ] All agent time filter formats present in mapping
  - [ ] Function returns correct format for each agent

---

#### Module 1.4: Debug Configuration
- **File**: `src/debug_config.py`
- **Purpose**: Global debug flags for development (fake responses, logging, etc.)
- **Key Class**: `DebugConfig` dataclass
- **Flags**:
  - `DEBUG` - master debug switch
  - `fake_response_enabled` - use cached API responses
  - `fake_response_update` - refresh cache on next call
  - `fake_response_interact` - ask user interactively before each operation
  - `log_*` flags - fine-grained logging control
- **What to Check**:
  - All flags initialized with sensible defaults
  - `enable_debug()`, `disable_debug()` methods work
  - `set_update_mode()` method correctly sets flags
  - No side effects when flags are changed
- **Dependencies**: None (pure configuration)
- **Verification**:
  - [ ] `DebugConfig.DEBUG` defaults to False
  - [ ] `DebugConfig.fake_response_enabled` defaults to False
  - [ ] `enable_debug()` sets both DEBUG and fake_response_enabled to True
  - [ ] All methods exist and are callable

---

#### Module 1.5: Scheduler Configuration
- **File**: `src/scheduler/config.py`
- **Purpose**: Scheduler-specific configuration and agent setup
- **Key Class**: `SchedulerConfig`
- **What to Check**:
  - Loads API keys from environment
  - Maps agent names to configurations
  - `get_agent_configs()` returns all 6 agents
  - Handles missing API keys gracefully
- **Dependencies**: `src.enums`, `src.utils`, `os`, `dotenv`
- **Verification**:
  - [ ] `SchedulerConfig` class exists
  - [ ] `get_agent_configs()` function returns dict
  - [ ] All 6 agent configs present (even if keys are missing)
  - [ ] No unhandled exceptions when API keys missing

---

### PHASE 2: Utilities & Helpers (4 modules)

These modules provide utility functions and debug infrastructure.

#### Module 2.1: Fake Response Manager
- **File**: `src/utils/fake_response_manager.py`
- **Purpose**: Manage cached API responses for development without making real API calls
- **Key Class**: `FakeResponseManager`
- **Key Methods**:
  - `generate_hash(url, method, description)` - MD5 hash of request parameters
  - `get_response(agent_name, url, method, description)` - retrieve cached response
  - `save_response()` - store new response
  - `update_response()` - replace existing response (single-file update)
  - `list_responses(agent_name)` - list all cached responses
  - `get_statistics(agent_name)` - usage statistics
- **Storage Format**: `data/fake_response/{agent_name}/{md5_hash}.json` + `.metadata.json`
- **What to Check**:
  - MD5 hash generation is deterministic (same input = same hash)
  - Response files are valid JSON
  - Metadata files track usage correctly
  - Directory structure exists for all agents: bocha/, xunfei/, hunyuan/, qianfan/, meta/, twitter/
- **Global Instance**: `fake_response_manager` singleton
- **Dependencies**: `src.utils.debug_logger`, `hashlib`, `json`, `pathlib`
- **Verification**:
  - [ ] `FakeResponseManager` class exists
  - [ ] `generate_hash()` produces consistent 32-character MD5 hashes
  - [ ] `fake_response_manager` singleton accessible from `src.utils`
  - [ ] BOCHA test response exists: `data/fake_response/bocha/5469eca43510d6e40651b0c7a226b65e.json`
  - [ ] Test: `from src.utils import fake_response_manager` works

---

#### Module 2.2: Debug Logger
- **File**: `src/utils/debug_logger.py`
- **Purpose**: Color-coded console logging for development
- **Key Class**: `DebugLogger`
- **Key Methods**:
  - `debug(message)` - cyan colored debug output
  - `info(message)` - green colored info output
  - `warning(message)` - yellow colored warning output
  - `error(message)` - red colored error output
- **Key Functions**:
  - `print_debug_header(text)` - print section header
  - `print_debug_info(key, value)` - print key-value pair
  - `print_debug_warning(message)` - print warning
  - `print_debug_error(message)` - print error
  - `print_debug_success(message)` - print success message
- **What to Check**:
  - Logger respects `DebugConfig.DEBUG` flag
  - ANSI color codes used correctly (cyan, green, yellow, red)
  - Timestamp format consistent [HH:MM:SS]
  - No output when DEBUG disabled
- **Dependencies**: `src.debug_config`, `datetime`
- **Verification**:
  - [ ] `DebugLogger` class instantiable with module name
  - [ ] Methods don't raise exceptions
  - [ ] When `DebugConfig.DEBUG = True`, output is visible
  - [ ] When `DebugConfig.DEBUG = False`, no output

---

#### Module 2.3: Utils Package Init
- **File**: `src/utils/__init__.py`
- **Purpose**: Convert utils/ directory to Python package and re-export modules
- **What to Check**:
  - Exports `FakeResponseManager` and `fake_response_manager`
  - Exports `DebugLogger` and debug printing functions
  - Note in comments about avoiding circular imports with utils.py
  - Original utils.py functions still accessible separately
- **Dependencies**: `.fake_response_manager`, `.debug_logger`
- **Verification**:
  - [ ] `from src.utils import fake_response_manager` works
  - [ ] `from src.utils import FakeResponseManager` works
  - [ ] `from src.utils import DebugLogger` works
  - [ ] No circular import errors

---

#### Module 2.4: Response Handler Decorator
- **File**: `src/decorators/response_handler.py`
- **Purpose**: Decorator for transparent API response caching
- **Key Decorator**: `@fake_response_handler(agent_name, url, method, description)`
- **Logic Flow**:
  1. Check if `fake_response_enabled` flag is True
  2. Generate MD5 hash from (url, method, description)
  3. Try to load cached response
  4. If found: optionally ask user interactively, return cached response
  5. If not found: call real API, optionally cache result
- **Helper Functions**:
  - `_ask_user_choice()` - interactive prompt (f)ake/(r)eal/(u)pdate/(s)kip
  - `_cache_response()` - save response to cache
- **What to Check**:
  - Decorator preserves function signature with `@functools.wraps`
  - User interaction prompts are clear and informative
  - Cache lookups are efficient (MD5-based)
  - No modification to agent core logic
- **Dependencies**: `functools`, `src.debug_config`, `src.utils.fake_response_manager`, `src.utils.debug_logger`
- **Verification**:
  - [ ] `from src.decorators import fake_response_handler` works
  - [ ] Decorator accepts all required parameters
  - [ ] Decorator doesn't break function execution
  - [ ] User prompts appear when `fake_response_interact = True`

---

### PHASE 3: Data Models (3 modules)

These dataclasses define the core data structures used throughout the system.

#### Module 3.1: Config Dataclasses
- **File**: `src/dataclasses/config.py`
- **Purpose**: Configuration dataclasses for each agent (BOCHA, XUNFEI, HUNYUAN, QIANFAN, META, TWITTER)
- **Key Dataclasses**:
  - `AgentConfig` - base agent configuration with name, api_key, api_url
  - `BOCHA_CONFIG`, `XUNFEI_CONFIG`, `HUNYUAN_CONFIG`, `QIANFAN_CONFIG`, `META_CONFIG`, `TWITTER_CONFIG`
- **What to Check**:
  - Each agent config has proper API endpoint URL
  - API keys loaded from environment variables
  - Config dataclasses are immutable (frozen=True)
  - All 6 agents configured
- **Dependencies**: `dataclasses`, `src.debug_config`
- **Verification**:
  - [ ] `from src.dataclasses.config import BOCHA_CONFIG` works
  - [ ] BOCHA_CONFIG has correct API URL
  - [ ] All 6 agent configs importable
  - [ ] Configs are dataclass instances

---

#### Module 3.2: Request/Response Dataclasses
- **File**: `src/dataclasses/dataclasses.py`
- **Purpose**: Query and response data structures
- **Key Dataclasses**:
  - `SearchItem` - individual search result (title, source_name, description, url, date_published)
  - `QueryRequest` - user query parameters (query_fields, query_topics, source_agents, days_back, max_results, language)
  - `QueryResponse` - agent response (agent_name, items, query_params, timestamp, budget_used, success)
- **What to Check**:
  - All fields have proper type hints
  - Dataclasses are properly structured
  - No circular references between dataclasses
  - Serialization methods work (if present)
- **Dependencies**: `dataclasses`, `datetime`, `typing`
- **Verification**:
  - [ ] `from src.dataclasses import SearchItem` works
  - [ ] `from src.dataclasses import QueryRequest` works
  - [ ] `from src.dataclasses import QueryResponse` works
  - [ ] Can instantiate each dataclass with test data

---

#### Module 3.3: Database Model Classes
- **File**: `src/dataclasses/models.py`
- **Purpose**: SQLite ORM-style model definitions
- **Key Classes**:
  - `QueryModel` - stores query records
  - `ResponseModel` - stores agent responses
  - `SearchItemModel` - stores individual search items
  - `SourceModel` - stores data source information
- **What to Check**:
  - Model classes have clear field definitions
  - Primary key and relationships defined
  - Methods for insertion, retrieval exist
- **Dependencies**: `src.dataclasses.dataclasses`, `sqlite3`, `datetime`
- **Verification**:
  - [ ] `from src.dataclasses.models import QueryModel` works
  - [ ] All model classes importable
  - [ ] Models have __init__ and data conversion methods

---

### PHASE 4: Database Layer (3 modules)

These modules handle data persistence.

#### Module 4.1: Database Backend (Abstract)
- **File**: `src/database/backend.py`
- **Purpose**: Abstract base class for database implementations
- **Key Class**: `DatabaseBackend` (abstract)
- **Key Methods** (abstract):
  - `save_query()` - store QueryRequest
  - `save_response()` - store QueryResponse
  - `save_item()` - store SearchItem
  - `get_items_by_source()` - retrieve items
  - `delete_query()` - remove query
- **What to Check**:
  - All methods are abstract (raise NotImplementedError)
  - Docstrings explain contract
  - No concrete implementation in this class
- **Dependencies**: `abc` module
- **Verification**:
  - [ ] `from src.database.backend import DatabaseBackend` works
  - [ ] Cannot instantiate abstract class directly
  - [ ] Subclasses can override methods

---

#### Module 4.2: SQLite Implementation
- **File**: `src/database/sqlite_backend.py`
- **Purpose**: Concrete SQLite3 implementation of database backend
- **Key Class**: `SQLiteBackend`
- **Database Schema**:
  - `queries` table - stores QueryRequest records
  - `responses` table - stores QueryResponse records
  - `items` table - stores SearchItem records
  - `sources` table - stores source information
- **Key Methods**:
  - Connection management (open, close)
  - Schema initialization
  - CRUD operations for all entities
- **What to Check**:
  - Database file path configurable
  - Tables created with proper schema
  - Indices exist for efficient queries
  - No cascade relationships (per user requirement)
  - Transactions handled properly
- **Dependencies**: `sqlite3`, `src.database.backend`, `src.dataclasses`
- **Verification**:
  - [ ] `from src.database.sqlite_backend import SQLiteBackend` works
  - [ ] Can instantiate with database path
  - [ ] Database file created on first use
  - [ ] All tables initialized correctly

---

#### Module 4.3: Database Manager
- **File**: `src/database/manager.py`
- **Purpose**: Facade for database operations with context manager support
- **Key Class**: `DatabaseManager`
- **Key Features**:
  - Context manager protocol (`__enter__`, `__exit__`)
  - Lazy loading of backend
  - Transaction management
  - Error handling
- **Key Methods**:
  - All backend methods delegated through this class
  - `initialize()` - setup database
  - `close()` - cleanup connections
- **What to Check**:
  - Context manager works correctly
  - Backend properly initialized and cleaned up
  - Error handling doesn't leak resources
- **Dependencies**: `src.database.backend`, `src.database.sqlite_backend`
- **Verification**:
  - [ ] `from src.database import DatabaseManager` works
  - [ ] Can use with `with DatabaseManager(...) as db:` syntax
  - [ ] No connection leaks

---

### PHASE 5: Agent System (6 modules)

These modules implement the core search agent system.

#### Module 5.1: Abstract Base Agent
- **File**: `src/agents/base.py`
- **Purpose**: Abstract base class for all search agents
- **Key Class**: `SearchAgent` (abstract)
- **Key Abstract Methods**:
  - `submit_request(query, request)` - send request to API
  - `parse_response(response)` - parse API response
- **Properties**:
  - `name` - agent name (BOCHA, XUNFEI, etc.)
  - `config` - AgentConfig instance
- **What to Check**:
  - All abstract methods properly declared
  - Cannot be instantiated directly
  - Subclasses provide implementations
- **Dependencies**: `abc`, `src.dataclasses`
- **Verification**:
  - [ ] `from src.agents.base import SearchAgent` works
  - [ ] Is abstract (cannot instantiate)
  - [ ] Has required abstract methods

---

#### Module 5.2: BOCHA Agent
- **File**: `src/agents/bocha.py`
- **Purpose**: Concrete implementation for Bocha search API
- **Key Class**: `BochaAgent(SearchAgent)`
- **Decorator**: `@fake_response_handler` on `submit_request()` method
- **Key Methods**:
  - `submit_request()` - call Bocha API (with decorator)
  - `parse_response()` - extract SearchItems from response
- **What to Check**:
  - Inherits from SearchAgent
  - Decorator applied to submit_request
  - Response parsing returns QueryResponse with SearchItems
  - Error handling for API failures
  - Rate limiting and budget tracking
- **Dependencies**: `src.agents.base`, `src.dataclasses`, `src.decorators`, `requests`
- **Verification**:
  - [ ] `from src.agents.bocha import BochaAgent` works
  - [ ] Can instantiate with BochaAgent(BOCHA_CONFIG)
  - [ ] Has @fake_response_handler decorator
  - [ ] Can call submit_request() without real API calls (if fake responses enabled)

---

#### Module 5.3-5.7: Other Agents (XUNFEI, HUNYUAN, QIANFAN, META, TWITTER)
- **Files**: `src/agents/xunfei.py`, `src/agents/hunyuan.py`, `src/agents/qianfan.py`, `src/agents/meta.py`, `src/agents/twitter.py`
- **Purpose**: Concrete implementations for other search APIs
- **Status**: 📌 **MISSING** - Not yet implemented
- **What to Check** (when implemented):
  - Each agent properly inherits from SearchAgent
  - Each has appropriate decorator
  - Response parsing matches API format
  - Error handling for rate limits and authentication
- **Note**: These are placeholder references. Full implementation needed.

---

#### Module 5.8: Agent Configuration Manager
- **File**: `src/agents/config_manager.py`
- **Purpose**: Centralized management of agent configurations
- **Key Class**: `AgentConfigManager`
- **Key Methods**:
  - `get_ready_agents()` - agents with API keys configured
  - `get_unavailable_agents()` - agents missing credentials
  - `initialize_agents()` - create agent instances
- **What to Check**:
  - Loads all 6 agent configs
  - Filters by API key availability
  - Instantiates agents correctly
- **Dependencies**: `src.dataclasses.config`, `src.agents.base`, all agent implementations
- **Verification**:
  - [ ] `from src.agents.config_manager import AgentConfigManager` works
  - [ ] Can call `get_ready_agents()` without exceptions
  - [ ] Returns list of available agents

---

#### Module 5.9: Template Engine
- **File**: `src/agents/template_engine.py`
- **Purpose**: Jinja2-based prompt templating for LLM agents
- **Key Class**: `TemplateEngine`
- **Templates**:
  - `config/templates/xunfei_template.jinja2` - XUNFEI prompt template
  - `config/templates/hunyuan_template.jinja2` - HUNYUAN prompt template
  - `config/templates/qianfan_template.jinja2` - QIANFAN prompt template
- **Key Methods**:
  - `render(template_name, **context)` - render template with context
  - `register_template(name, template_str)` - add custom template
- **What to Check**:
  - Templates load from config/templates/
  - Jinja2 syntax valid
  - Context variables properly substituted
  - No template injection vulnerabilities
- **Dependencies**: `jinja2`, `src.debug_config`
- **Verification**:
  - [ ] `from src.agents.template_engine import TemplateEngine` works
  - [ ] Templates directory exists
  - [ ] Can render templates without errors

---

### PHASE 6: Orchestration & CLI (8 modules)

These modules tie everything together and provide the user interface.

#### Module 6.1: Search Pipeline
- **File**: `src/pipeline.py`
- **Purpose**: Orchestrate multi-agent parallel search and result aggregation
- **Key Class**: `SearchPipeline`
- **Key Methods**:
  - `execute(query)` - run search across all selected agents
  - `aggregate_results()` - combine and deduplicate results
  - `apply_filters()` - filter by time, source, etc.
- **What to Check**:
  - Agents run in parallel (if async enabled)
  - Results properly aggregated
  - Deduplication by URL or title hash
  - Error handling for individual agent failures
- **Dependencies**: `src.database.manager`, `src.agents`, `src.dataclasses`
- **Verification**:
  - [ ] `from src.pipeline import SearchPipeline` works
  - [ ] Can instantiate and call execute()
  - [ ] Returns aggregated QueryResponse

---

#### Module 6.2: Scheduler Main
- **File**: `src/scheduler/scheduler.py`
- **Purpose**: Main scheduler orchestrator with interactive menu
- **Key Class**: `Scheduler`
- **Key Methods**:
  - `print_briefing()` - system initialization report
  - `show_main_menu()` - display menu options
  - `run()` - main event loop
  - `cleanup()` - resource cleanup
- **What to Check**:
  - Initializes all actions (explore, submit_query, export, stats, settings)
  - Displays formatted menu
  - Routes user choices to appropriate actions
  - Handles errors gracefully
- **Dependencies**: `src.scheduler.actions.*`, `src.database.manager`, `src.scheduler.interactive`
- **Verification**:
  - [ ] `from src.scheduler.scheduler import Scheduler` works
  - [ ] Can instantiate and call run()
  - [ ] Menu displays all 5 actions

---

#### Module 6.3: Scheduler Settings
- **File**: `src/scheduler/scheduler_settings.py`
- **Purpose**: Configuration management from .env file
- **Key Classes**:
  - `EnvironmentVariables` - all env var definitions
  - `SchedulerSettings` - settings manager
- **Key Methods**:
  - `initialize(env_file)` - load from .env
  - `get_ready_agents()` - agents with keys
  - `validate_critical_config()` - check essentials
  - `full_initialization_report()` - complete status
- **What to Check**:
  - Loads from .env file correctly
  - All environment variables parsed
  - Missing keys handled gracefully
  - Validation methods work
- **Dependencies**: `dotenv`, `src.dataclasses.config`, `pathlib`
- **Verification**:
  - [ ] `from src.scheduler.scheduler_settings import SchedulerSettings` works
  - [ ] Can load from .env file
  - [ ] Displays ready agents correctly

---

#### Module 6.4: Interactive UI
- **File**: `src/scheduler/interactive.py`
- **Purpose**: Color-coded terminal UI components
- **Key Functions**:
  - `prompt_choice(options)` - user selection menu
  - `prompt_text(message)` - text input
  - `prompt_list(items)` - list selection
  - `prompt_confirm(message)` - yes/no confirmation
  - `print_header(text)` - section header
  - `print_section(title, items)` - formatted section
  - `print_table(headers, rows)` - formatted table
- **What to Check**:
  - ANSI color codes applied correctly
  - Input validation for choices
  - Clear prompts and output
  - No exceptions on invalid input
- **Dependencies**: None (pure UI functions)
- **Verification**:
  - [ ] `from src.scheduler.interactive import prompt_choice` works
  - [ ] All UI functions callable
  - [ ] Output is colored and readable

---

#### Module 6.5: Scheduler Actions - Base
- **File**: `src/scheduler/actions/base.py`
- **Purpose**: Abstract base class for all scheduler actions
- **Key Class**: `Action` (abstract)
- **Key Properties**:
  - `name` - action display name
  - `description` - action description
- **Key Abstract Methods**:
  - `execute()` - action implementation
- **What to Check**:
  - Abstract class properly defined
  - Properties return strings
  - Cannot be instantiated directly
- **Dependencies**: `abc`
- **Verification**:
  - [ ] `from src.scheduler.actions.base import Action` works
  - [ ] Is abstract

---

#### Module 6.6: Scheduler Actions - Explore
- **File**: `src/scheduler/actions/explore.py`
- **Purpose**: Browse research history and query results
- **Key Class**: `ExploreAction(Action)`
- **Sub-menus**:
  - Recent queries
  - Recent responses
  - Items by source
  - Search items
- **What to Check**:
  - Reads from database correctly
  - Formats output nicely
  - Handles empty results
  - Pagination if needed
- **Dependencies**: `src.scheduler.actions.base`, `src.database.manager`, `src.scheduler.interactive`
- **Verification**:
  - [ ] Can instantiate ExploreAction
  - [ ] execute() method works
  - [ ] No database errors

---

#### Module 6.7: Scheduler Actions - Submit Query
- **File**: `src/scheduler/actions/submit_query.py`
- **Purpose**: Guided query submission (8 steps)
- **Key Class**: `SubmitQueryAction(Action)`
- **Step Sequence**:
  1. Select agents (BOCHA, XUNFEI, etc.)
  2. Enter query fields
  3. Enter query topics
  4. Select time filter
  5. Set result limits
  6. Review query
  7. Preview templates
  8. Execute and store results
- **What to Check**:
  - Each step validates input
  - Can go back and edit
  - Integration with SearchPipeline
  - Results stored in database
- **Dependencies**: `src.scheduler.actions.base`, `src.pipeline`, `src.dataclasses`
- **Verification**:
  - [ ] Can instantiate SubmitQueryAction
  - [ ] Execute step works (or shows wizard)
  - [ ] Handles user input correctly

---

#### Module 6.8: Scheduler Actions - Export
- **File**: `src/scheduler/actions/export.py`
- **Purpose**: Export query results to JSON/Markdown
- **Key Class**: `ExportAction(Action)`
- **Export Formats**:
  - JSON - structured data export
  - Markdown - human-readable format with tables
- **Export Scopes**:
  - All items
  - By source
  - By query
- **What to Check**:
  - JSON valid and properly formatted
  - Markdown readable and well-structured
  - Files saved to `data/` directory
  - Handles special characters
- **Dependencies**: `src.scheduler.actions.base`, `src.database.manager`, `json`, `pathlib`
- **Verification**:
  - [ ] Can instantiate ExportAction
  - [ ] Execute generates files
  - [ ] Output files are valid

---

#### Module 6.9: Scheduler Actions - Stats
- **File**: `src/scheduler/actions/stats.py`
- **Purpose**: Display database statistics
- **Key Class**: `StatsAction(Action)`
- **Statistics Shown**:
  - Total queries run
  - Total responses collected
  - Total items stored
  - Breakdown by agent
  - Breakdown by source
- **What to Check**:
  - Calculates stats correctly
  - Displays in readable format
  - Handles empty database
- **Dependencies**: `src.scheduler.actions.base`, `src.database.manager`
- **Verification**:
  - [ ] Can instantiate StatsAction
  - [ ] Execute returns stats
  - [ ] Numbers are accurate

---

#### Module 6.10: Scheduler Actions - Settings
- **File**: `src/scheduler/actions/settings.py`
- **Purpose**: View agent capabilities and configuration
- **Key Class**: `SettingsAction(Action)`
- **Information Shown**:
  - Agent names and capabilities
  - API key status (configured/missing)
  - API endpoint URLs
  - Rate limits and quotas
- **What to Check**:
  - Shows all 6 agents
  - Indicates which have API keys
  - Clear format
- **Dependencies**: `src.scheduler.actions.base`, `src.scheduler.scheduler_settings`
- **Verification**:
  - [ ] Can instantiate SettingsAction
  - [ ] Execute shows agent info

---

#### Module 6.11: CLI Entry Point
- **File**: `examples/scheduler.py`
- **Purpose**: Main command-line entry point for the scheduler
- **Key Features**:
  - Argument parsing (--env, --db, --show-env, --show-env-vars)
  - Environment setup and validation
  - Full initialization report
  - Error handling and user guidance
- **Flags**:
  - `--env FILE` - specify .env file path
  - `--db PATH` - specify database path
  - `--show-env` - show loaded environment
  - `--show-env-vars` - show all env variables
- **What to Check**:
  - Argument parsing works
  - All flags functional
  - Initialization report displays
  - Error messages are helpful
- **Dependencies**: `src.scheduler.scheduler`, `src.scheduler.scheduler_settings`, `argparse`
- **Verification**:
  - [ ] `python -m examples.scheduler` runs
  - [ ] Help text displays: `python -m examples.scheduler --help`
  - [ ] Can specify custom .env and database paths

---

#### Module 6.12: Basic Example
- **File**: `examples/basic_example.py`
- **Purpose**: Demonstration of programmatic usage (non-CLI)
- **Shows**:
  - How to create agents manually
  - How to submit queries
  - How to access results
  - How to use database directly
- **What to Check**:
  - Example code is runnable
  - Shows real use case
  - Comments explain each step
- **Dependencies**: All core modules
- **Verification**:
  - [ ] `python -m examples.basic_example` runs
  - [ ] No unhandled exceptions

---

### Test Modules (Verification Only)

#### Test Module T1: Fake Response Tests
- **File**: `examples/test_fake_response.py`
- **Purpose**: Comprehensive test suite for fake response system
- **Tests** (10 total):
  1. Module imports
  2. MD5 hash generation
  3. Existing responses listing
  4. Response retrieval
  5. Debug configuration
  6. Response statistics
  7. Existence checking
  8. Directory structure
  9. Decorator imports
  10. Debug logger
- **Command**: `python -m examples.test_fake_response`
- **Expected Output**: ✅ ALL TESTS PASSED!
- **Verification**:
  - [ ] All 10 tests pass
  - [ ] No error messages

---

#### Test Module T2: Scheduler Settings Tests
- **File**: `examples/test_scheduler_settings.py`
- **Purpose**: Test configuration loading and validation
- **Tests** (10 total):
  - Environment variable parsing
  - Agent status checking
  - Database validation
  - Export directory creation
  - API key status
  - Ready agents filtering
  - Initialization reports
- **Command**: `python -m examples.test_scheduler_settings`
- **Expected Output**: ✅ ALL TESTS PASSED!
- **Verification**:
  - [ ] All tests pass
  - [ ] No configuration errors

---

## Dependency Graph

```
┌─────────────────────────────────────────┐
│        Dependency Hierarchy             │
└─────────────────────────────────────────┘

Level 0: Foundation (No dependencies)
├── config/.env.example
├── src/enums.py
└── src/utils.py

Level 1: Debug & Logging (depends on Level 0)
├── src/debug_config.py
├── src/utils/debug_logger.py
└── src/decorators/response_handler.py

Level 2: Data Management (depends on Levels 0-1)
├── src/utils/fake_response_manager.py
├── src/dataclasses/config.py
├── src/dataclasses/dataclasses.py
└── src/dataclasses/models.py

Level 3: Database (depends on Levels 0-2)
├── src/database/backend.py
├── src/database/sqlite_backend.py
└── src/database/manager.py

Level 4: Agents (depends on Levels 0-3)
├── src/agents/base.py
├── src/agents/bocha.py
├── src/agents/xunfei.py (missing)
├── src/agents/hunyuan.py (missing)
├── src/agents/qianfan.py (missing)
├── src/agents/meta.py (missing)
├── src/agents/twitter.py (missing)
├── src/agents/config_manager.py
└── src/agents/template_engine.py

Level 5: Orchestration (depends on Levels 0-4)
├── src/pipeline.py
├── src/scheduler/config.py
├── src/scheduler/scheduler_settings.py
└── src/scheduler/interactive.py

Level 6: CLI & Actions (depends on All levels)
├── src/scheduler/scheduler.py
├── src/scheduler/actions/base.py
├── src/scheduler/actions/explore.py
├── src/scheduler/actions/submit_query.py
├── src/scheduler/actions/export.py
├── src/scheduler/actions/stats.py
├── src/scheduler/actions/settings.py
├── examples/scheduler.py
└── examples/basic_example.py

Level 7: Tests (depends on Levels 0-6)
├── examples/test_fake_response.py
└── examples/test_scheduler_settings.py

CIRCULAR DEPENDENCIES: NONE DETECTED ✅
```

---

## Known Issues & Missing Components

### ⚠️ Missing Agent Implementations

The following agents are not yet implemented but are referenced in the architecture:

| Agent | Status | File | Priority |
|-------|--------|------|----------|
| BOCHA | ✅ Complete | `src/agents/bocha.py` | - |
| XUNFEI | 📌 Missing | `src/agents/xunfei.py` | High |
| HUNYUAN | 📌 Missing | `src/agents/hunyuan.py` | High |
| QIANFAN | 📌 Missing | `src/agents/qianfan.py` | High |
| META | 📌 Missing | `src/agents/meta.py` | High |
| TWITTER | 📌 Missing | `src/agents/twitter.py` | High |

**Impact**: System works with BOCHA only. Other agents configured but non-functional until implementations added.

---

### ✅ Verified Working Components

- [x] Foundation configuration (enums, utils, debug config)
- [x] Fake response system (all 10 tests passing)
- [x] Debug logging infrastructure
- [x] Data models (SearchItem, QueryRequest, QueryResponse)
- [x] Database layer (SQLite backend with no cascades)
- [x] BOCHA agent with decorator
- [x] Scheduler core orchestration
- [x] CLI entry point
- [x] Interactive UI
- [x] Settings management from .env
- [x] All 5 scheduler actions

---

### 📋 Recommended Implementation Order

1. **Phase 1-3**: Foundation ✅ (Complete)
2. **Phase 4-5**: Database & BOCHA Agent ✅ (Complete)
3. **Phase 6**: Scheduler & CLI ✅ (Complete)
4. **Missing**: Implement remaining 5 agents (XUNFEI, HUNYUAN, QIANFAN, META, TWITTER)

---

## Verification Checklist

### Quick Verification (5 minutes)

- [ ] Clone/navigate to project
- [ ] Ensure .env file exists with API keys
- [ ] Run Phase 1 checks (config files exist)
- [ ] Run `python -m examples.test_fake_response` - should pass all 10 tests
- [ ] Run `python -m examples.test_scheduler_settings` - should pass all tests

### Full Verification (2-3 hours)

Use the checklist items listed under each module in the phase-by-phase section above.

### Per-Phase Verification

After completing each phase:

- [ ] **Phase 1**: All foundation modules importable
- [ ] **Phase 2**: All utilities work without errors
- [ ] **Phase 3**: All dataclasses instantiable
- [ ] **Phase 4**: Database operations functional
- [ ] **Phase 5**: BOCHA agent can submit requests (with fake responses)
- [ ] **Phase 6**: Scheduler CLI starts and displays menu

---

## Testing Commands

```bash
# Test fake response system
python -m examples.test_fake_response

# Test scheduler settings
python -m examples.test_scheduler_settings

# Run scheduler CLI
python -m examples.scheduler

# Run basic example
python -m examples.basic_example

# Show environment variables (if configured)
python -m examples.scheduler --show-env-vars
```

---

## Next Steps

1. **Review this guide** - familiarize yourself with module structure
2. **Run quick verification** - confirm system works
3. **Module-by-module checking** - follow phase-by-phase section
4. **Implement missing agents** - add XUNFEI, HUNYUAN, QIANFAN, META, TWITTER
5. **Expand test coverage** - add tests for missing agents
6. **Performance optimization** - parallel agent execution, result caching
7. **Documentation** - keep module docstrings updated

---

## Summary

This guide provides a systematic way to understand and verify the NewsAgent project:

- **29 modules** organized into **6 phases**
- **Clean dependency hierarchy** with zero circular dependencies
- **All core components working** - foundation, utilities, database, BOCHA agent, scheduler
- **Missing components identified** - 5 additional agents need implementation
- **Comprehensive test coverage** - 20+ tests for core functionality

Use this guide to methodically review the codebase, understand the architecture, and verify everything works as expected.

**Happy checking! 🚀**
