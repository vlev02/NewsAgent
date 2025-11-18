# Environment Override Quick Reference

## TL;DR

Test specific functionality without modifying global `.env` file:

```python
from src.scheduler.scheduler_settings import SchedulerSettings

settings = SchedulerSettings.initialize(
    database_path="data/test.db",  # Override specific values
    log_level="DEBUG"               # Inherit rest from .env
)
```

---

## Problem

You want to test features like `fake_response` with custom settings while inheriting most configuration from `.env`, without modifying the global `.env` file.

## Solution

NewsAgent provides a **single entry point** for environment configuration with built-in override support:

```python
SchedulerSettings.initialize(env_file=".env", **overrides)
```

---

## Usage Patterns

### Pattern 1: Default (use .env as-is)

```python
settings = SchedulerSettings.initialize()
```

### Pattern 2: Override specific values

```python
settings = SchedulerSettings.initialize(
    database_path="data/demo.db",
    log_level="DEBUG",
    bocha_api_key="test-key"
)
```

### Pattern 3: Use different .env file

```python
settings = SchedulerSettings.initialize(".env.production")
```

### Pattern 4: Custom file + overrides

```python
settings = SchedulerSettings.initialize(
    ".env.staging",
    database_path="data/staging.db"
)
```

---

## Complete Example: Fake Response Testing

```python
"""
Test fake_response without modifying global .env
"""

from src.scheduler.scheduler_settings import SchedulerSettings
from src.debug_config import DebugConfig

# 1. Load environment with overrides
settings = SchedulerSettings.initialize(
    database_path="data/demo_fake_response.db",  # Use test database
    log_level="DEBUG"                            # Increase verbosity
)

# 2. Configure debug flags (not in .env)
DebugConfig.DEBUG = True
DebugConfig.fake_response_enabled = True
DebugConfig.fake_response_update = True

# 3. Use agents normally - responses will be cached
from src.agents.bocha import BochaAgent

ready_agents = settings.get_ready_agents()
bocha_agent = BochaAgent(ready_agents["BOCHA"])

# First call: Real API (or cached if exists)
response = bocha_agent.submit_and_parse(query)

# Second call: Instant from cache
response = bocha_agent.submit_and_parse(query)
```

Run the complete demo:
```bash
python examples/demo_fake_response.py
```

---

## Available Override Keys

### API Keys
- `xunfei_appid`, `xunfei_api_secret`, `xunfei_api_key`, `xunfei_api_password`
- `hunyuan_secret_id`, `hunyuan_secret_key`, `hunyuan_api_key`
- `bocha_api_key`
- `qianfan_api_key`
- `meta_api_key`
- `twitter_bearer_token`

### Configuration
- `database_path` (str)
- `log_level` (str): "DEBUG", "INFO", "WARNING", "ERROR"
- `log_file` (str)
- `export_directory` (str)
- `default_time_range_days` (int)
- `default_max_results` (int)
- `http_proxy` (str)
- `https_proxy` (str)

---

## Override Priority

Settings are applied in this order (highest priority first):

```
**overrides (highest)
    ↓
.env file variables
    ↓
Default values (lowest)
```

---

## Common Use Cases

### Use Case 1: Testing with different database

```python
settings = SchedulerSettings.initialize(
    database_path="data/test.db"
)
```

### Use Case 2: Testing with mock API key

```python
settings = SchedulerSettings.initialize(
    bocha_api_key="mock-key-for-testing"
)
```

### Use Case 3: Debugging with verbose logging

```python
settings = SchedulerSettings.initialize(
    log_level="DEBUG",
    log_file="debug.log"
)
```

### Use Case 4: Testing fake response caching

```python
settings = SchedulerSettings.initialize(
    database_path="data/demo.db",
    log_level="DEBUG"
)

DebugConfig.fake_response_enabled = True
DebugConfig.fake_response_update = True
```

### Use Case 5: Production deployment

```python
settings = SchedulerSettings.initialize(
    ".env.production",
    log_level="WARNING"
)
```

---

## Benefits

✅ **Single entry point** - No confusion about where to load environment
✅ **Explicit overrides** - Clear what's being changed
✅ **Clean API** - Pythonic `**kwargs` pattern
✅ **Type-safe** - IDE autocomplete on EnvironmentVariables fields
✅ **No file proliferation** - No need for `.env.test`, `.env.local`, etc.
✅ **Testable** - Easy to mock or override in tests

---

## Related Documentation

- Full guide: `docs/CONFIGURATION_GUIDE.md`
- Demo script: `examples/demo_fake_response.py`
- Fake response manual: `docs/FAKE_RESPONSE_MANUAL.md`
- Scheduler settings: `src/scheduler/scheduler_settings.py`

---

## Troubleshooting

### Invalid override key warning

```python
# ⚠️  Unknown override key: invalid_key (ignored)
```

**Cause:** The key is not a field in `EnvironmentVariables` dataclass.

**Solution:** Check available keys in "Available Override Keys" section above.

### Override not taking effect

**Cause:** Override might be spelled incorrectly or applied after initialization.

**Solution:** Apply overrides during `initialize()` call:

```python
# ❌ Wrong - too late
settings = SchedulerSettings.initialize()
settings.env_vars.database_path = "data/test.db"  # Too late!

# ✅ Correct - during initialization
settings = SchedulerSettings.initialize(
    database_path="data/test.db"
)
```

### API key not loading

**Cause:** .env file not found or not loaded.

**Solution:** Ensure .env file exists in project root:

```bash
# Check if .env exists
ls -la .env

# If not, copy from example
cp .env.example .env

# Edit with your keys
nano .env
```
