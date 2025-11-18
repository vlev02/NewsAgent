#!/usr/bin/env python3
"""
Test script to debug fake response caching issue.
"""

import sys
from pathlib import Path
import json

# Add project root to path
# Works whether script is run from root or from scripts/ directory
project_root = Path(__file__).parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.scheduler.scheduler_settings import SchedulerSettings
from src.debug_config import DebugConfig
from src.dataclasses import QueryRequest
from src.agents.bocha import BochaAgent
from src.utils import fake_response_manager

print("=" * 70)
print("TEST: Fake Response Caching")
print("=" * 70)
print()

# 1. Setup
print("Step 1: Setup")
print("-" * 70)
settings = SchedulerSettings.initialize()
ready_agents = settings.get_ready_agents()
bocha_config = ready_agents["BOCHA"]
bocha_agent = BochaAgent(bocha_config)
print(f"✓ BOCHA agent initialized")
print()

# 2. Enable caching
print("Step 2: Enable Caching")
print("-" * 70)
DebugConfig.DEBUG = True
DebugConfig.fake_response_enabled = True
DebugConfig.fake_response_update = True
DebugConfig.fake_response_interact = False
print(f"✓ Caching enabled")
print(f"  fake_response_enabled: {DebugConfig.fake_response_enabled}")
print(f"  fake_response_update: {DebugConfig.fake_response_update}")
print()

# 3. Create query
print("Step 3: Create Query")
print("-" * 70)
query = QueryRequest(
    query_fields=["自动驾驶"],
    query_topics=["特斯拉FSD"],
    source_agents=["BOCHA"],
    days_back=7,
    max_results=3,
    include_ai_summary=True,
    include_raw_response=True,
    language="zh"
)
print(f"✓ Query created: {query.query_id}")
print()

# 4. Check cache before
print("Step 4: Check Cache Before")
print("-" * 70)
cached_before = fake_response_manager.list_responses("BOCHA")
print(f"Cached responses before: {len(cached_before)}")
if cached_before:
    for c in cached_before:
        print(f"  - {c.get('md5_hash', 'N/A')}: {c.get('description', 'N/A')}")
print()

# 5. Call API
print("Step 5: Call API (call_api method)")
print("-" * 70)
try:
    # Build query
    query_string = " ".join(query.query_fields + query.query_topics)
    print(f"Query string: {query_string}")
    print()

    # Call pure API
    print("Calling bocha_agent.call_api()...")
    raw_response = bocha_agent.call_api(query_string, query)

    print(f"✓ API call successful")
    print(f"  Response type: {type(raw_response).__name__}")
    print(f"  Response keys: {list(raw_response.keys()) if isinstance(raw_response, dict) else 'N/A'}")
    print()

    if isinstance(raw_response, dict) and 'webPages' in raw_response:
        print(f"  webPages keys: {list(raw_response['webPages'].keys())}")
        print(f"  Total matches: {raw_response['webPages'].get('totalEstimatedMatches', 'N/A')}")
        print(f"  Results: {len(raw_response['webPages'].get('value', []))}")
    print()

except Exception as e:
    print(f"❌ Error calling API: {e}")
    import traceback
    traceback.print_exc()
    print()

# 6. Check cache after
print("Step 6: Check Cache After")
print("-" * 70)
cached_after = fake_response_manager.list_responses("BOCHA")
print(f"Cached responses after: {len(cached_after)}")
if cached_after:
    for c in cached_after:
        print(f"  - {c.get('md5_hash', 'N/A')}: {c.get('description', 'N/A')}")
        print(f"    Created: {c.get('created', 'N/A')}")
        print(f"    Size: {c.get('size_bytes', 'N/A')} bytes")
else:
    print("❌ NO CACHE CREATED")
print()

# 7. Check cache files
print("Step 7: Check Cache Files")
print("-" * 70)
import os
cache_dir = Path("data/fake_response/bocha")
if cache_dir.exists():
    files = list(cache_dir.glob("*"))
    print(f"Files in {cache_dir}: {len(files)}")
    for f in files:
        print(f"  - {f.name} ({f.stat().st_size} bytes)")
else:
    print(f"Cache directory doesn't exist: {cache_dir}")
print()

# 8. Summary
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Cache created: {'YES ✓' if len(cached_after) > len(cached_before) else 'NO ❌'}")
if len(cached_after) > len(cached_before):
    print("Fake response caching is working correctly!")
else:
    print("Fake response caching is NOT working.")
    print("Possible reasons:")
    print("  1. API call failed (check error above)")
    print("  2. DebugConfig.fake_response_update is False")
    print("  3. Response is already cached")
    print("  4. fake_response_manager failed to save")
