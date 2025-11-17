#!/usr/bin/env python3
"""
Test script to verify scheduler components work correctly.
"""

import sys
from pathlib import Path

# Test imports
print("=" * 70)
print("Testing Scheduler Components")
print("=" * 70)
print()

try:
    print("Testing imports...")
    from src.scheduler import Scheduler
    from src.scheduler.config import SchedulerConfig, get_agent_configs
    from src.scheduler.interactive import (
        print_header, print_section, print_success, print_error
    )
    from src.scheduler.actions import (
        ExploreAction, SubmitQueryAction, ExportAction,
        StatsAction, SettingsAction
    )
    print("✅ All scheduler modules imported successfully")
    print()

except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test configuration
try:
    print("Testing configuration...")
    config = SchedulerConfig.from_env()
    print(f"✅ Configuration loaded: db={config.database_path}")

    agents_config = get_agent_configs()
    print(f"✅ Agent configs loaded: {len(agents_config)} agents")
    print()

except Exception as e:
    print(f"❌ Configuration failed: {e}")
    sys.exit(1)

# Test database connection
try:
    print("Testing database connection...")
    from src.database import SQLite3Backend, DatabaseManager

    # Use in-memory database for testing
    test_db = DatabaseManager(SQLite3Backend(":memory:"))
    test_db.connect()
    print("✅ Database connection successful")

    stats = test_db.get_stats()
    print(f"✅ Database stats: {stats['total_queries']} queries, {stats['total_items']} items")

    test_db.disconnect()
    print()

except Exception as e:
    print(f"❌ Database test failed: {e}")
    sys.exit(1)

# Test scheduler initialization
try:
    print("Testing scheduler initialization...")

    from src.database import SQLite3Backend, DatabaseManager

    # Create test scheduler with in-memory database
    test_db = DatabaseManager(SQLite3Backend(":memory:"))
    test_db.connect()

    config = SchedulerConfig.from_env()
    agents_config = get_agent_configs()

    # Create scheduler manually (don't run interactive loop)
    scheduler = Scheduler(config, agents_config)
    print("✅ Scheduler initialized successfully")

    # Verify actions
    print(f"✅ Actions registered: {len(scheduler.actions)}")
    for action in scheduler.actions:
        print(f"   - {action.name}: {action.description}")

    scheduler.cleanup()
    print()

except Exception as e:
    print(f"❌ Scheduler initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test action instantiation
try:
    print("Testing action instantiation...")

    from src.database import SQLite3Backend, DatabaseManager

    test_db = DatabaseManager(SQLite3Backend(":memory:"))
    test_db.connect()

    agents_config = get_agent_configs()

    actions = [
        ExploreAction(test_db, agents_config),
        SubmitQueryAction(test_db, agents_config),
        ExportAction(test_db, agents_config),
        StatsAction(test_db, agents_config),
        SettingsAction(test_db, agents_config),
    ]

    for action in actions:
        print(f"✅ {action.name}")

    test_db.disconnect()
    print()

except Exception as e:
    print(f"❌ Action instantiation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Summary
print("=" * 70)
print("✅ ALL SCHEDULER TESTS PASSED!")
print("=" * 70)
print()
print("You can now run the scheduler with:")
print("  python -m examples.scheduler")
print()
