#!/usr/bin/env python3
"""
Simple test script to verify all imports and basic functionality work.
"""

import sys
from datetime import datetime


def test_imports():
    """Test that all modules import correctly"""
    print("Testing imports...")

    try:
        from src.dataclasses import SearchItem, QueryRequest, QueryResponse
        print("✅ Dataclasses imported successfully")
    except Exception as e:
        print(f"❌ Failed to import dataclasses: {e}")
        return False

    try:
        from src.dataclasses.config import BOCHA_CONFIG
        print("✅ Agent configs imported successfully")
    except Exception as e:
        print(f"❌ Failed to import agent configs: {e}")
        return False

    try:
        from src.agents.base import SearchAgent
        print("✅ SearchAgent base class imported successfully")
    except Exception as e:
        print(f"❌ Failed to import SearchAgent: {e}")
        return False

    try:
        from src.agents.bocha import BochaAgent
        print("✅ BochaAgent imported successfully")
    except Exception as e:
        print(f"❌ Failed to import BochaAgent: {e}")
        return False

    try:
        from src.database import DatabaseBackend, SQLite3Backend, DatabaseManager
        print("✅ Database classes imported successfully")
    except Exception as e:
        print(f"❌ Failed to import database classes: {e}")
        return False

    try:
        from src.pipeline import SearchPipeline
        print("✅ SearchPipeline imported successfully")
    except Exception as e:
        print(f"❌ Failed to import SearchPipeline: {e}")
        return False

    return True


def test_dataclass_creation():
    """Test that dataclasses can be instantiated"""
    print("\nTesting dataclass instantiation...")

    try:
        from src.dataclasses import SearchItem, QueryRequest, QueryResponse

        # Create a SearchItem
        item = SearchItem(
            title="Test Article",
            content="This is a test",
            source_url="https://example.com",
            source_name="Example",
            source_type="BOCHA",
            timestamp=datetime.now()
        )
        print(f"✅ SearchItem created: {item.id}")

        # Create a QueryRequest
        request = QueryRequest(
            query_fields=["test"],
            query_topics=["example"],
            source_agents=["BOCHA"]
        )
        print(f"✅ QueryRequest created: {request.query_id}")

        # Create a QueryResponse
        response = QueryResponse(
            agent_name="BOCHA",
            query_id=request.query_id,
            items=[item],
            success=True
        )
        print(f"✅ QueryResponse created: {response.response_id}")

        return True
    except Exception as e:
        print(f"❌ Failed to create dataclasses: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_creation():
    """Test that agents can be instantiated"""
    print("\nTesting agent creation...")

    try:
        from src.dataclasses.config import BOCHA_CONFIG
        from src.agents.bocha import BochaAgent

        config = BOCHA_CONFIG
        config.api_key = "test-key"
        agent = BochaAgent(config)
        print(f"✅ BochaAgent created: {agent.config.agent_name}")

        return True
    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database():
    """Test database creation and operations"""
    print("\nTesting database...")

    try:
        from src.database import SQLite3Backend, DatabaseManager
        from src.dataclasses import QueryRequest, SearchItem
        from datetime import datetime

        # Create in-memory database for testing
        db = DatabaseManager(SQLite3Backend(":memory:"))
        db.connect()

        # Create and save a query
        request = QueryRequest(
            query_fields=["test"],
            query_topics=["example"],
            source_agents=["BOCHA"]
        )
        saved_id = db.save_query(request)
        print(f"✅ Query saved: {saved_id}")

        # Create and save an item
        item = SearchItem(
            title="Test Item",
            content="Test content",
            source_url="https://example.com",
            source_name="Example",
            source_type="BOCHA",
            timestamp=datetime.now()
        )
        saved_item_id = db.save_item(item)
        print(f"✅ Item saved: {saved_item_id}")

        # Load and verify
        loaded_query = db.load_query(saved_id)
        if loaded_query:
            print(f"✅ Query loaded: {loaded_query.query_id}")
        else:
            print("❌ Failed to load query")
            return False

        db.disconnect()
        return True
    except Exception as e:
        print(f"❌ Failed database test: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 70)
    print("NEWSAGENT MODULE TEST SUITE")
    print("=" * 70)

    results = {
        "Imports": test_imports(),
        "Dataclass Creation": test_dataclass_creation(),
        "Agent Creation": test_agent_creation(),
        "Database": test_database(),
    }

    print("\n" + "=" * 70)
    print("TEST RESULTS")
    print("=" * 70)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")

    all_passed = all(results.values())
    print("\n" + ("=" * 70))
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
