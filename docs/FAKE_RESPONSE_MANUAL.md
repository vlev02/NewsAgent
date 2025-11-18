# Fake Response System - Simple Manual

## What Is It?

A development tool that caches API responses so you can test without making real API calls.

**Benefits:**
- No API costs during development
- Instant response (no network delay)
- Test with consistent data
- Control what data you work with

---

## Quick Start (3 Steps)

### Step 1: Enable Fake Responses
```python
from src.debug_config import DebugConfig

DebugConfig.fake_response_enabled = True
```

### Step 2: Run Your Code
```python
from src.agents.bocha import BochaAgent
from src.dataclasses.config import BOCHA_CONFIG
from src.dataclasses import QueryRequest

# Create agent
agent = BochaAgent(BOCHA_CONFIG)

# Create query
query = QueryRequest(
    query_fields=["auto driving"],
    query_topics=["Tesla FSD"],
    source_agents=["BOCHA"],
    days_back=7,
    max_results=10
)

# Run - will use cached response if available
response = agent.submit_request(query.query_fields[0], query)
```

### Step 3: Check the Response
```python
print(f"Got {len(response.items)} items from cache")
for item in response.items:
    print(f"- {item.title}")
```

---

## How It Works

```
Your Code
   ↓
@fake_response_handler decorator (intercepts the call)
   ↓
Check: Is response cached?
   ├─ YES → Return cached response
   └─ NO  → Call real API (if fake_response_update=True)
```

---

## Common Use Cases

### Use Case 1: Test Code Without API Calls

**Scenario:** You're developing features but don't want to waste API quota

```python
from src.debug_config import DebugConfig

# Turn on caching
DebugConfig.fake_response_enabled = True

# Your code works with cached responses
agent = BochaAgent(config)
results = agent.submit_request(query_str, request)

# Process results as normal
for item in results.items:
    print(item.title)
```

---

### Use Case 2: See What's Cached

**Scenario:** You want to know what fake responses are available

```python
from src.utils import fake_response_manager

# List all cached BOCHA responses
responses = fake_response_manager.list_responses("BOCHA")

for resp in responses:
    print(f"Description: {resp['description']}")
    print(f"Used {resp['usage_count']} times")
    print(f"Created: {resp['created']}")
    print()
```

**Output:**
```
Description: default
Used 2 times
Created: 2025-11-17T13:54:00

...
```

---

### Use Case 3: Debug with Console Output

**Scenario:** You want to see what's happening (cache hits, misses, etc.)

```python
from src.debug_config import DebugConfig

# Enable debug mode
DebugConfig.DEBUG = True
DebugConfig.log_fake_response_hits = True
DebugConfig.log_fake_response_misses = True

# Your code
agent = BochaAgent(config)
results = agent.submit_request(query_str, request)
```

**Console output:**
```
[13:54:00] [INFO] [response_handler] Cache HIT: bocha/b597eeb470d45a99d
[13:54:00] [DEBUG] [decorator] Using cached response
```

---

### Use Case 4: Refresh One Cached Response

**Scenario:** The cached response is outdated, refresh just that one

```python
from src.debug_config import DebugConfig

# Tell system to update cache on next call
DebugConfig.fake_response_enabled = True
DebugConfig.fake_response_update = True

# This will:
# 1. Call real API
# 2. Save response to cache
# 3. Return the fresh response
agent = BochaAgent(config)
fresh_results = agent.submit_request(query_str, request)

# From now on, use the cached version
DebugConfig.fake_response_update = False
results2 = agent.submit_request(query_str, request)  # Uses cache
```

---

### Use Case 5: Ask Me For Each Decision

**Scenario:** You want to manually choose fake or real for each call

```python
from src.debug_config import DebugConfig

# Enable interactive mode
DebugConfig.DEBUG = True
DebugConfig.fake_response_interact = True

# When you call the agent, it will ask:
agent = BochaAgent(config)
results = agent.submit_request(query_str, request)

# You'll see:
# Found cached response for this request.
# (f)ake - Use cached response
# (r)eal - Call real API
# (u)pdate - Call real API and update cache
# (s)kip - Don't ask again this session
# Enter choice:
```

Just type `f`, `r`, `u`, or `s` and press Enter.

---

## Decorator Usage (For Developers)

### Option 1: Auto-Extract from Config (Recommended)

The decorator can automatically extract agent name, URL, and description from the instance:

```python
from src.decorators import fake_response_handler

class MyAgent(SearchAgent):
    @fake_response_handler()  # No parameters needed!
    def submit_request(self, query, request):
        # Decorator auto-extracts:
        # - agent_name from self.config.agent_name
        # - url from self.config.api_endpoint
        # - description from function name ("submit_request")

        response = requests.post(
            self.config.api_endpoint,
            json=body,
            headers=self.get_header_dict()
        )
        return response.json()
```

### Option 2: Hardcode Values (Backward Compatible)

You can still specify values explicitly:

```python
@fake_response_handler(
    agent_name="BOCHA",
    url="https://api.bocha.ai/search",
    method="POST",
    description="default"
)
def submit_request(self, query, request):
    # ...
```

### How It Works

When you use `@fake_response_handler()` with no arguments:

1. **agent_name**: Extracted from `self.config.agent_name`
2. **url**: Extracted from `self.config.api_endpoint`
3. **description**: Uses the function name (e.g., `"submit_request"`)
4. **method**: Defaults to `"POST"`

This means cache files are automatically named based on your agent configuration!

---

## Configuration Flags

Simple reference of what each flag does:

```python
from src.debug_config import DebugConfig

# Main switch
DebugConfig.DEBUG = True/False
  # When True: shows colored console output
  # When False: quiet, no output

DebugConfig.fake_response_enabled = True/False
  # When True: uses cached responses if available
  # When False: always calls real API

DebugConfig.fake_response_update = True/False
  # When True: calls real API and updates cache
  # When False: keeps existing cache

DebugConfig.fake_response_interact = True/False
  # When True: asks you before each operation (requires DEBUG=True)
  # When False: automatic decisions

# Logging (only works when DEBUG=True)
DebugConfig.log_fake_response_hits = True/False
DebugConfig.log_fake_response_misses = True/False
DebugConfig.log_api_calls = True/False
```

---

## Example: Complete Testing Session

Here's a real example from start to finish:

```python
from src.debug_config import DebugConfig
from src.agents.bocha import BochaAgent
from src.dataclasses.config import BOCHA_CONFIG
from src.dataclasses import QueryRequest
from src.utils import fake_response_manager

print("=== Testing BOCHA Agent ===\n")

# Step 1: Check what we have cached
print("Step 1: Check cached responses")
responses = fake_response_manager.list_responses("BOCHA")
print(f"Found {len(responses)} cached responses\n")

# Step 2: Enable fake responses and debug
print("Step 2: Enable fake responses")
DebugConfig.fake_response_enabled = True
DebugConfig.DEBUG = True
DebugConfig.log_fake_response_hits = True
print("Fake responses: ON")
print("Debug logging: ON\n")

# Step 3: Create agent and query
print("Step 3: Create query and run")
agent = BochaAgent(BOCHA_CONFIG)
query = QueryRequest(
    query_fields=["auto driving"],
    query_topics=["Tesla FSD"],
    source_agents=["BOCHA"],
    days_back=7,
    max_results=10
)

# This will use cached response
results = agent.submit_request(
    query.query_fields[0] + " " + query.query_topics[0],
    query
)

# Step 4: Process results
print(f"\nStep 4: Got {len(results.items)} items\n")
for item in results.items:
    print(f"✓ {item.title}")
    print(f"  From: {item.source_name}")
    print()

# Step 5: Check stats
print("Step 5: Statistics")
stats = fake_response_manager.get_statistics("BOCHA")
print(f"Total cached responses: {stats['total_cached']}")
print(f"Total usage: {stats['total_usage']}")
print(f"Average usage: {stats.get('average_usage', 0):.1f}")
```

**Console output:**
```
=== Testing BOCHA Agent ===

Step 1: Check cached responses
Found 1 cached responses

Step 2: Enable fake responses
Fake responses: ON
Debug logging: ON

Step 3: Create query and run
[13:54:00] [INFO] [response_handler] Cache HIT: bocha/b597eeb...

Step 4: Got 3 items

✓ Tesla FSD Latest Updates and Developments
  From: Tesla News

✓ Humanoid Robots Make Progress in Physical Tasks
  From: AI Research

✓ Autonomous Vehicle Safety Standards Updated
  From: Industry News

Step 5: Statistics
Total cached responses: 1
Total usage: 2
Average usage: 2.0
```

---

## File Structure

Where are the cached responses stored?

```
data/fake_response/
└── bocha/
    ├── b597eeb470d45a99d6297bf53e533da8.json
    │   └─ Contains: request_body and response_body
    └── b597eeb470d45a99d6297bf53e533da8.metadata.json
        └─ Contains: usage_count, created, last_used, notes
```

**To view a cached response:**
```bash
cat data/fake_response/bocha/b597eeb470d45a99d6297bf53e533da8.json
```

---

## Testing Without Writing Code

You can test the system without writing code:

```bash
# Run the test suite
python -m examples.test_fake_response

# Output:
# ✅ Test 1: Importing fake response manager
# ✅ Test 2: Testing MD5 hash generation
# ✅ Test 3: Checking existing fake responses
# ... (10 tests total)
# ✅ ALL TESTS PASSED!
```

---

## Troubleshooting

### "I don't see any cached responses"

```python
from src.utils import fake_response_manager

# Check if directory exists
responses = fake_response_manager.list_responses("BOCHA")
print(f"Found: {len(responses)} responses")

# If 0, enable update mode to create cache
from src.debug_config import DebugConfig
DebugConfig.fake_response_enabled = True
DebugConfig.fake_response_update = True

# Next call will cache the response
agent = BochaAgent(config)
results = agent.submit_request(query_str, request)
print("Response cached!")
```

### "Cache isn't being used"

Check these settings:

```python
from src.debug_config import DebugConfig

# Make sure enabled
print(f"Enabled: {DebugConfig.fake_response_enabled}")

# Enable debug to see what's happening
DebugConfig.DEBUG = True

# Run again - you should see console output
agent = BochaAgent(config)
results = agent.submit_request(query_str, request)
```

### "I want to see what's happening"

```python
from src.debug_config import DebugConfig

# Turn on all logging
DebugConfig.DEBUG = True
DebugConfig.log_fake_response_hits = True
DebugConfig.log_fake_response_misses = True
DebugConfig.log_api_calls = True
DebugConfig.log_decorator_calls = True

# Now you'll see colored output for everything
```

---

## Summary

| Want to... | Do this |
|-----------|--------|
| Use cached responses | `DebugConfig.fake_response_enabled = True` |
| See debug output | `DebugConfig.DEBUG = True` |
| Refresh cache | `DebugConfig.fake_response_update = True` |
| Ask me before each call | `DebugConfig.fake_response_interact = True` (needs DEBUG=True) |
| List cached responses | `fake_response_manager.list_responses("BOCHA")` |
| Get statistics | `fake_response_manager.get_statistics("BOCHA")` |
| Check what's cached | `cat data/fake_response/bocha/[hash].json` |

---

## Key Points to Remember

✓ **Cached responses are stored as JSON files** - easy to view and edit
✓ **Each agent has its own folder** - bocha/, xunfei/, etc.
✓ **Cache is keyed by URL + method + description** - same query = same file
✓ **No external dependencies** - pure Python and files
✓ **Safe by default** - caching disabled until you enable it
✓ **Can update one file at a time** - doesn't affect other caches

---

## Next Steps

1. Enable fake responses: `DebugConfig.fake_response_enabled = True`
2. Run your code as normal
3. Check console output with `DebugConfig.DEBUG = True`
4. View cached responses: `fake_response_manager.list_responses("BOCHA")`
5. Refresh if needed: `DebugConfig.fake_response_update = True`
