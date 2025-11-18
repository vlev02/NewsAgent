# Configuration Guide

## Overview

NewsAgent uses a centralized configuration system where **all agent settings are defined in a single YAML file**: `config/agents.yaml`.

## Configuration Architecture

```
config/agents.yaml         ← SINGLE SOURCE OF TRUTH
        ↓
src/dataclasses/config.py  ← Loads YAML at import time
        ↓
Agent instances            ← Use loaded AgentConfig objects
```

## How It Works

1. **At startup**, `src/dataclasses/config.py` reads `config/agents.yaml`
2. **Parses YAML** structure into `AgentConfig` dataclass instances
3. **Exports** individual config variables (`BOCHA_CONFIG`, `XUNFEI_CONFIG`, etc.)
4. **Agents** use these config objects when initialized

## config/agents.yaml Structure

```yaml
agents:
  AGENT_NAME:
    name: "Human-readable name"
    enabled: true/false
    type: "LLM_SEARCH" | "REST_API" | "SOCIAL_MEDIA"
    endpoint: "https://api.example.com/endpoint"
    capabilities:
      supports_time_filter: true/false
      supports_ai_summary: true/false
      supports_streaming: true/false
      needs_json_extraction: true/false
    defaults:
      # Agent-specific default parameters
      model: "model-name"
      temperature: 0.3
      count: 10
```

## Supported Agents

| Agent | Type | Endpoint |
|-------|------|----------|
| **XUNFEI** | LLM_SEARCH | Xunfei Spark API |
| **BOCHA** | REST_API | BOCHA Web Search |
| **HUNYUAN** | LLM_SEARCH | Tencent Hunyuan |
| **QIANFAN** | LLM_SEARCH | Baidu Qianfan |
| **META** | REST_API | MetaSo Search |
| **TWITTER** | SOCIAL_MEDIA | Twitter/X API v2 |

## How to Modify Configurations

### 1. Edit config/agents.yaml

```yaml
agents:
  BOCHA:
    endpoint: "https://api.bochaai.com/v1/web-search"  # Change endpoint
    defaults:
      count: 20  # Change from 10 to 20
      summary: false  # Disable AI summary
```

### 2. Restart Application

Configurations are loaded at import time, so you need to restart:

```bash
# If running as script
python your_script.py  # Restart

# If in Python shell
exit()  # Exit and re-enter
python
```

### 3. Changes Take Effect

All agents will now use the updated settings from the YAML file.

## Environment Configuration

### Single Entry Point Pattern

NewsAgent uses a **unified environment loading system** with a single entry point:

```python
from src.scheduler.scheduler_settings import SchedulerSettings

# This is the SINGLE way to load environment configuration
settings = SchedulerSettings.initialize()
```

### API Keys and Environment Variables

API keys are **NOT** stored in `config/agents.yaml`. They are loaded from environment variables via `.env` file:

```bash
# .env file
BOCHA_API_KEY=your_api_key_here
XUNFEI_APPID=your_appid_here
QIANFAN_API_KEY=your_api_key_here
# ... etc
```

### Environment Override Pattern

To test specific functionality without modifying the global `.env` file, use the `**overrides` parameter:

```python
# Load from .env with specific overrides
settings = SchedulerSettings.initialize(
    database_path="data/test.db",
    log_level="DEBUG",
    bocha_api_key="test-key"
)
```

### Override Examples

#### Example 1: Use default .env
```python
settings = SchedulerSettings.initialize()
```

#### Example 2: Use custom .env file
```python
settings = SchedulerSettings.initialize(".env.production")
```

#### Example 3: Override specific values (inherits rest from .env)
```python
settings = SchedulerSettings.initialize(
    database_path="data/test.db",
    log_level="DEBUG",
    bocha_api_key="override-key"
)
```

#### Example 4: Combine custom file + overrides
```python
settings = SchedulerSettings.initialize(
    ".env.staging",
    database_path="data/staging.db"
)
```

### Supported Override Keys

All fields from `EnvironmentVariables` dataclass can be overridden:

**API Keys:**
- `xunfei_appid`, `xunfei_api_secret`, `xunfei_api_key`, `xunfei_api_password`
- `hunyuan_secret_id`, `hunyuan_secret_key`, `hunyuan_api_key`
- `bocha_api_key`
- `qianfan_api_key`
- `meta_api_key`
- `twitter_bearer_token`

**Configuration:**
- `database_path` (str)
- `log_level` (str)
- `log_file` (str)
- `export_directory` (str)
- `default_time_range_days` (int)
- `default_max_results` (int)
- `http_proxy` (str)
- `https_proxy` (str)

### Override Priority

Settings are applied in this order (highest priority first):

1. **`**overrides`** - Keyword arguments to `initialize()`
2. **Environment variables** - From .env file
3. **Default values** - Defined in `EnvironmentVariables` dataclass

### Testing Pattern

For testing with fake responses without modifying global `.env`:

```python
from src.scheduler.scheduler_settings import SchedulerSettings
from src.debug_config import DebugConfig

# Initialize with test-specific overrides
settings = SchedulerSettings.initialize(
    database_path="data/demo_fake_response.db",
    log_level="DEBUG"
)

# Configure debug flags (not in .env)
DebugConfig.DEBUG = True
DebugConfig.fake_response_enabled = True
DebugConfig.fake_response_update = True

# Your test code here...
```

See `examples/demo_fake_response.py` for a complete demonstration.

## Example: Adding a New Agent

1. **Add to config/agents.yaml**:

```yaml
agents:
  # ... existing agents ...
  
  NEW_AGENT:
    name: "My New Search API"
    enabled: true
    type: "REST_API"
    endpoint: "https://api.newsearch.com/v1/search"
    capabilities:
      supports_time_filter: true
      supports_ai_summary: false
      supports_streaming: false
      needs_json_extraction: false
    defaults:
      max_results: 10
      language: "en"
```

2. **Add API key to .env**:

```bash
NEW_AGENT_API_KEY=your_api_key_here
```

3. **Update `src/scheduler/config.py`**:

```python
def get_agent_configs():
    configs = {
        # ... existing ...
        "NEW_AGENT": NEW_AGENT_CONFIG,
    }
    
    for name, config in configs.items():
        # ... existing logic ...
        elif name == "NEW_AGENT":
            config.api_key = os.getenv("NEW_AGENT_API_KEY")
```

4. **Implement agent class** in `src/agents/new_agent.py`

5. **Restart application**

## Benefits of YAML Configuration

✅ **Single source of truth** - All settings in one place  
✅ **Easy to modify** - Edit YAML instead of Python code  
✅ **Version control friendly** - Track config changes in git  
✅ **No hardcoded values** - All settings externalized  
✅ **Type-safe** - YAML parsed into dataclass instances  
✅ **Backward compatible** - Existing code works without changes

## Migration from Hardcoded Configs

Previously, agent configurations were hardcoded in `src/dataclasses/config.py` as Python objects. Now they're loaded from YAML.

**Old approach** (deprecated):
```python
BOCHA_CONFIG = AgentConfig(
    agent_name="BOCHA",
    agent_type="REST_API",
    api_endpoint="https://...",
    # ... 20+ lines of hardcoded settings
)
```

**New approach** (current):
```yaml
# config/agents.yaml
agents:
  BOCHA:
    type: "REST_API"
    endpoint: "https://..."
    # Clean, readable YAML structure
```

The Python module automatically creates `BOCHA_CONFIG` by loading the YAML file.
