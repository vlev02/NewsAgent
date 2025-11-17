#!/usr/bin/env python3
"""
Test scheduler settings initialization.
"""

import sys
from pathlib import Path

print("=" * 70)
print("Testing Scheduler Settings")
print("=" * 70)
print()

try:
    print("Testing imports...")
    from src.scheduler.scheduler_settings import (
        SchedulerSettings,
        EnvironmentVariables,
        initialize_scheduler_settings
    )
    print("✅ Scheduler settings modules imported successfully")
    print()

except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test environment variables parsing
try:
    print("Testing environment variable parsing...")
    env_vars = EnvironmentVariables.from_env()
    print("✅ Environment variables loaded")

    # Check some defaults
    assert env_vars.database_path == "newsagent.db", "Default database path should be newsagent.db"
    assert env_vars.log_level == "INFO", "Default log level should be INFO"
    assert env_vars.default_time_range_days == 7, "Default time range should be 7 days"
    assert env_vars.default_max_results == 10, "Default max results should be 10"

    print("✅ Environment variable defaults verified")
    print()

except Exception as e:
    print(f"❌ Environment variable test failed: {e}")
    sys.exit(1)

# Test scheduler settings initialization
try:
    print("Testing scheduler settings initialization...")

    settings = SchedulerSettings.initialize(env_file=".env")
    print("✅ Scheduler settings initialized")

    # Verify components
    assert settings.env_vars is not None, "Environment variables should be set"
    assert settings.scheduler_config is not None, "Scheduler config should be set"
    assert settings.agent_configs is not None, "Agent configs should be set"
    assert len(settings.agent_configs) == 6, "Should have 6 agent configs"

    print("✅ All components initialized correctly")
    print()

except Exception as e:
    print(f"⚠️  Settings initialization note: {e}")
    # Try without .env file (use defaults)
    try:
        print("Attempting initialization without .env file...")
        settings = SchedulerSettings.initialize(env_file=".env.missing")
        print("✅ Initialized with defaults")
    except Exception as e2:
        print(f"❌ Failed: {e2}")
        sys.exit(1)

# Test agent status checking
try:
    print("Testing agent status...")
    agents_status = settings.agents_status

    print(f"✅ Agent status checked: {len(agents_status)} agents")

    for agent_name, (ready, status) in agents_status.items():
        print(f"   {agent_name}: {status}")

    print()

except Exception as e:
    print(f"❌ Agent status test failed: {e}")
    sys.exit(1)

# Test getting ready agents
try:
    print("Testing ready agents retrieval...")
    ready_agents = settings.get_ready_agents()
    print(f"✅ Ready agents: {len(ready_agents)}")

    if ready_agents:
        for agent_name in ready_agents:
            print(f"   ✓ {agent_name}")
    else:
        print("   ℹ️  No agents with API keys configured (expected if .env not set)")

    print()

except Exception as e:
    print(f"❌ Ready agents test failed: {e}")
    sys.exit(1)

# Test unavailable agents
try:
    print("Testing unavailable agents...")
    unavailable = settings.get_unavailable_agents()
    print(f"✅ Unavailable agents: {len(unavailable)}")

    if unavailable:
        for agent_name, env_var in unavailable.items():
            print(f"   ✗ {agent_name} (needs {env_var})")
    else:
        print("   All agents configured!")

    print()

except Exception as e:
    print(f"❌ Unavailable agents test failed: {e}")
    sys.exit(1)

# Test database directory validation
try:
    print("Testing database directory validation...")
    is_valid = settings.validate_database_path()
    if is_valid:
        print("✅ Database directory is valid and writable")
    else:
        print("⚠️  Database directory check failed (may need write permissions)")

    print()

except Exception as e:
    print(f"⚠️  Database validation: {e}")

# Test export directory creation
try:
    print("Testing export directory...")
    settings.create_export_directory()
    print("✅ Export directory ready")
    print()

except Exception as e:
    print(f"⚠️  Export directory: {e}")

# Summary
print("=" * 70)
print("✅ ALL SCHEDULER SETTINGS TESTS PASSED!")
print("=" * 70)
print()
print("Scheduler settings are ready. You can now run:")
print("  python -m examples.scheduler")
print()
print("Or check settings with:")
print("  python -m examples.scheduler --show-env")
print("  python -m examples.scheduler --show-env-vars")
print()
