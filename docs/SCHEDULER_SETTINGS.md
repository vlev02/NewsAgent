# Scheduler Settings Management

The Scheduler Settings system handles comprehensive initialization of all environment variables, configurations, and agent setups from a `.env` file.

## Quick Start

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your API keys
nano .env

# Run the scheduler (settings will be loaded automatically)
python -m examples.scheduler
```

## Environment Variables

### Complete Environment Variables Reference

All environment variables are loaded from the `.env` file in the project root.

#### XUNFEI Spark API
```env
XUNFEI_APPID=your_appid_here
XUNFEI_APISecret=your_api_secret_here
XUNFEI_APIKey=your_api_key_here
XUNFEI_APIPassword=your_api_password_here
```

#### Tencent Hunyuan API
```env
HUNYUAN_SECRET_ID=your_secret_id_here
HUNYUAN_SECRET_KEY=your_secret_key_here
HUNYUAN_API_KEY=your_api_key_here
```

#### BOCHA Web Search API
```env
BOCHA_API_KEY=your_api_key_here
```

#### Baidu Qianfan AppBuilder
```env
QIANFAN_API_KEY=your_api_key_here
```

#### MetaSo Search API
```env
META_API_KEY=your_api_key_here
```

#### Twitter/X API v2
```env
TWITTER_BEARER_TOKEN=your_bearer_token_here
```

#### Database & Logging Configuration
```env
DATABASE_PATH=newsagent.db
LOG_LEVEL=INFO
LOG_FILE=newsagent.log
EXPORT_DIRECTORY=data
```

#### Scheduler Defaults
```env
DEFAULT_TIME_RANGE=7
DEFAULT_MAX_RESULTS=10
```

#### Optional Proxy Configuration
```env
HTTP_PROXY=http://proxy.example.com:8080
HTTPS_PROXY=https://proxy.example.com:8080
```

## Architecture

### Core Components

#### `EnvironmentVariables` Dataclass
Container for all environment variables with type safety.

```python
from src.scheduler.scheduler_settings import EnvironmentVariables

env_vars = EnvironmentVariables.from_env()
print(env_vars.xunfei_appid)
print(env_vars.bocha_api_key)
```

#### `SchedulerSettings` Class
Complete settings manager with initialization and validation.

```python
from src.scheduler.scheduler_settings import SchedulerSettings

# Initialize from .env file
settings = SchedulerSettings.initialize(env_file=".env")

# Access components
print(settings.env_vars)           # Environment variables
print(settings.scheduler_config)   # Scheduler configuration
print(settings.agent_configs)      # Agent configurations
print(settings.agents_status)      # Agent readiness status
```

#### `initialize_scheduler_settings()` Function
Main entry point for initialization.

```python
from src.scheduler.scheduler_settings import initialize_scheduler_settings

settings = initialize_scheduler_settings(env_file=".env")
if settings:
    settings.print_summary()
```

### Workflow

```
1. Load .env file
   ↓
2. Parse environment variables
   ↓
3. Create EnvironmentVariables instance
   ↓
4. Initialize scheduler configuration
   ↓
5. Initialize all agent configurations
   ↓
6. Check agent status (API keys present)
   ↓
7. Create SchedulerSettings instance
```

## Usage Patterns

### Basic Initialization

```python
from src.scheduler.scheduler_settings import initialize_scheduler_settings

# Initialize from default .env file
settings = initialize_scheduler_settings()

# Or specify custom .env file
settings = initialize_scheduler_settings(env_file=".env.local")
```

### Check Agent Status

```python
# Get all agents with API keys configured
ready_agents = settings.get_ready_agents()
print(f"Ready agents: {list(ready_agents.keys())}")

# Get agents without API keys
unavailable = settings.get_unavailable_agents()
print(f"Missing API keys: {unavailable}")
```

### Print Configuration Status

```python
# Print summary of all settings
settings.print_summary()

# Print detailed environment variable status
settings.print_env_status()

# Run complete initialization report
settings.full_initialization_report()
```

### Access Individual Settings

```python
# Environment variables
print(settings.env_vars.database_path)
print(settings.env_vars.bocha_api_key)

# Scheduler configuration
print(settings.scheduler_config['default_time_range_days'])

# Agent configurations
bocha_config = settings.agent_configs['BOCHA']
print(bocha_config.api_key)

# Agent status
for agent_name, (ready, status) in settings.agents_status.items():
    print(f"{agent_name}: {status}")
```

### Use with Scheduler

```python
from src.scheduler import Scheduler
from src.scheduler.scheduler_settings import initialize_scheduler_settings

# Initialize settings
settings = initialize_scheduler_settings()

# Create scheduler with settings
scheduler = Scheduler(settings=settings)
scheduler.run()
```

## Command-Line Interface

### View Configuration Status

```bash
# Show scheduler configuration summary
python -m examples.scheduler --show-env

# Output:
# ======================================================================
#               NewsAgent Scheduler - Configuration Status
# ======================================================================
#
# → Scheduler Settings Summary
# Database Path: newsagent.db
# Log Level: INFO
# Export Directory: data
#
# → Agent Configuration Status
# Ready Agents: 6/6
#   BOCHA: ✓ Ready
#   XUNFEI: ✓ Ready
#   ...
```

### View Environment Variables

```bash
# Show detailed environment variable status
python -m examples.scheduler --show-env-vars

# Output:
# → Environment Variables Status
#
# XUNFEI:
#   XUNFEI_APPID: ✓ SET
#   XUNFEI_APISecret: ✓ SET
#   XUNFEI_APIKey: ✓ SET
#
# BOCHA:
#   BOCHA_API_KEY: ✓ SET
# ...
```

### Run Initialization Report

```bash
# Run with automatic initialization report
python -m examples.scheduler

# Output shows:
# 1. Scheduler settings summary
# 2. Environment variable status
# 3. System checks
#    - Database directory validation
#    - Export directory creation
#    - Proxy configuration (if set)
#    - Agent configuration validation
```

### Custom Environment File

```bash
# Use custom .env file
python -m examples.scheduler --env .env.production

# Use custom database
python -m examples.scheduler --db /data/prod.db
```

## Initialization Sequence

### 1. Environment Variable Loading

The scheduler automatically loads `.env` file using `python-dotenv`:

```python
from dotenv import load_dotenv
load_dotenv('.env')
```

### 2. Variable Parsing

All environment variables are parsed into the `EnvironmentVariables` dataclass with proper type conversion and defaults.

### 3. Configuration Initialization

Three levels of configuration are created:

- **Scheduler Config**: Database path, logging, defaults
- **Agent Configs**: 6 pre-configured agents with API keys set
- **Status Checking**: Which agents have API keys

### 4. Validation

Automatic checks:
- ✓ Database directory exists and is writable
- ✓ Export directory can be created
- ✓ At least one agent has API key configured
- ✓ Proxy configuration (if set)

### 5. Ready to Run

Once initialized, settings are passed to the Scheduler for operation.

## Validation and Error Handling

### Critical Validation

The system validates:

1. **Database Access**
   - Directory exists or can be created
   - Write permissions available
   - Path is writable

2. **Agent Configuration**
   - At least one agent has API key
   - Agent configs are properly initialized
   - Status is correctly determined

3. **System Resources**
   - Export directory can be created
   - Proxy settings are valid

### Error Handling

```python
# Graceful fallback if .env doesn't exist
settings = SchedulerSettings.initialize(env_file=".env.missing")

# Uses default values:
# - database_path: "newsagent.db"
# - log_level: "INFO"
# - default_time_range_days: 7
# - agents: All configured but no API keys

# Validation failures
if not settings.validate_critical_config():
    print("Configuration is invalid - check API keys")
```

## Advanced Configuration

### Multiple Environment Files

```bash
# Development
cp .env.example .env.dev
python -m examples.scheduler --env .env.dev

# Production
cp .env.example .env.prod
python -m examples.scheduler --env .env.prod

# Testing
cp .env.example .env.test
python -m examples.scheduler --env .env.test
```

### Environment-Specific Settings

```python
import os

# Load based on environment
env = os.getenv("NEWSAGENT_ENV", "development")
settings = SchedulerSettings.initialize(env_file=f".env.{env}")
```

### Programmatic Configuration Override

```python
settings = SchedulerSettings.initialize()

# Override specific settings
settings.env_vars.database_path = "/custom/path/news.db"
settings.env_vars.default_max_results = 50

# Settings remain valid and can be used
scheduler = Scheduler(settings=settings)
```

## Troubleshooting

### "No agents configured" Error

**Problem**: All agents show "✗ Missing API Key"

**Solution**:
1. Copy `.env.example` to `.env`
2. Edit `.env` and fill in at least one API key
3. Run `python -m examples.scheduler --show-env-vars` to verify

### "Database directory not writable" Warning

**Problem**: Cannot create or write to database directory

**Solution**:
1. Check directory permissions: `ls -ld /path/to/db/dir`
2. Change permissions: `chmod 755 /path/to/db/dir`
3. Or specify different database path in `.env`

### Environment Variables Not Loading

**Problem**: Settings show "NOT SET" for API keys

**Solution**:
1. Verify `.env` file exists in project root: `ls -la .env`
2. Check `.env` syntax (no quotes, simple KEY=VALUE format)
3. Verify variables aren't commented out (no leading #)
4. Run `python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('BOCHA_API_KEY'))"` to debug

## Best Practices

1. **Never Commit .env**
   - Add `.env` to `.gitignore`
   - Use `.env.example` as template
   - Share only example file

2. **Different Files for Environments**
   - `.env.development` for local testing
   - `.env.staging` for staging server
   - `.env.production` for production

3. **Regular Validation**
   - Run `--show-env` before important operations
   - Check agent status in Settings action
   - Review logs for configuration issues

4. **Security**
   - Store `.env` in secure location
   - Restrict file permissions: `chmod 600 .env`
   - Don't share API keys via email/chat
   - Rotate keys regularly

5. **Backup Configuration**
   - Keep backup of working `.env` files
   - Version control (private repo) for environment templates
   - Document required API keys for team

## API Reference

### EnvironmentVariables

```python
@dataclass
class EnvironmentVariables:
    # API Keys
    xunfei_appid: Optional[str]
    xunfei_api_key: Optional[str]
    bocha_api_key: Optional[str]
    hunyuan_api_key: Optional[str]
    qianfan_api_key: Optional[str]
    meta_api_key: Optional[str]
    twitter_bearer_token: Optional[str]

    # Configuration
    database_path: str
    log_level: str
    log_file: str
    export_directory: str
    default_time_range_days: int
    default_max_results: int

    # Proxy
    http_proxy: Optional[str]
    https_proxy: Optional[str]

    @classmethod
    def from_env() -> EnvironmentVariables
    def to_dict() -> Dict[str, Any]
```

### SchedulerSettings

```python
@dataclass
class SchedulerSettings:
    env_vars: EnvironmentVariables
    scheduler_config: Dict[str, Any]
    agent_configs: Dict[str, AgentConfig]
    agents_status: Dict[str, Tuple[bool, str]]

    @classmethod
    def initialize(env_file: str = ".env") -> SchedulerSettings

    # Status methods
    def get_ready_agents() -> Dict[str, AgentConfig]
    def get_unavailable_agents() -> Dict[str, str]

    # Validation methods
    def validate_critical_config() -> bool
    def validate_database_path() -> bool

    # Display methods
    def print_summary() -> None
    def print_env_status() -> None
    def full_initialization_report() -> bool

    # Setup methods
    def setup_proxies() -> None
    def create_export_directory() -> None
```

## Related Documentation

- [SCHEDULER.md](SCHEDULER.md) - Interactive scheduler user guide
- [README_NEW_ARCHITECTURE.md](README_NEW_ARCHITECTURE.md) - Overall architecture
- [.env.example](../.env.example) - Environment variable template

---

**Version**: 1.0
**Status**: Production-Ready
**Last Updated**: November 17, 2024
