#!/usr/bin/env python3
"""
Simple test script to verify all imports and basic functionality work.

Unit tests for module imports and basic dataclass/agent/database creation.
"""

import unittest
from datetime import datetime

from src.dataclasses import SearchItem, QueryRequest, QueryResponse
from src.database import DatabaseBackend, SQLite3Backend, DatabaseManager
from src.pipeline import SearchPipeline


class TestModuleImports(unittest.TestCase):
    """Test that all modules can be imported"""

    def test_dataclasses_import(self):
        """Test importing dataclasses"""
        self.assertIsNotNone(SearchItem)
        self.assertIsNotNone(QueryRequest)
        self.assertIsNotNone(QueryResponse)

    def test_database_import(self):
        """Test importing database classes"""
        self.assertIsNotNone(DatabaseBackend)
        self.assertIsNotNone(SQLite3Backend)
        self.assertIsNotNone(DatabaseManager)

    def test_pipeline_import(self):
        """Test importing SearchPipeline"""
        self.assertIsNotNone(SearchPipeline)


class TestDataclassCreation(unittest.TestCase):
    """Test that dataclasses can be instantiated"""

    def test_search_item_creation(self):
        """Test SearchItem instantiation"""
        item = SearchItem(
            title="Test Article",
            content="This is a test",
            source_url="https://example.com",
            source_name="Example",
            source_type="TestAgent",
            timestamp=datetime.now()
        )
        self.assertIsNotNone(item.id)
        self.assertEqual(item.title, "Test Article")
        self.assertEqual(item.source_name, "Example")

    def test_query_request_creation(self):
        """Test QueryRequest instantiation"""
        request = QueryRequest(
            query_fields=["test"],
            query_topics=["example"],
            source_agents=["TestAgent"]
        )
        self.assertIsNotNone(request.query_id)
        self.assertEqual(request.query_fields, ["test"])
        self.assertEqual(request.query_topics, ["example"])

    def test_query_response_creation(self):
        """Test QueryResponse instantiation"""
        item = SearchItem(
            title="Test",
            content="Test content",
            source_url="https://example.com",
            source_name="Example",
            source_type="TestAgent",
            timestamp=datetime.now()
        )
        request = QueryRequest(
            query_fields=["test"],
            query_topics=["example"],
            source_agents=["TestAgent"]
        )
        response = QueryResponse(
            agent_name="TestAgent",
            query_id=request.query_id,
            items=[item],
            success=True
        )
        self.assertIsNotNone(response.response_id)
        self.assertEqual(response.agent_name, "TestAgent")
        self.assertEqual(len(response.items), 1)

    def test_query_request_fields(self):
        """Test QueryRequest has required fields"""
        request = QueryRequest(
            query_fields=["field1", "field2"],
            query_topics=["topic1"],
            source_agents=["TestAgent"],
            days_back=7,
            max_results=10
        )
        self.assertEqual(len(request.query_fields), 2)
        self.assertEqual(request.days_back, 7)
        self.assertEqual(request.max_results, 10)

    def test_search_item_fields(self):
        """Test SearchItem has required fields"""
        now = datetime.now()
        item = SearchItem(
            title="Title",
            content="Content",
            source_url="https://example.com",
            source_name="Source",
            source_type="TestAgent",
            timestamp=now
        )
        self.assertEqual(item.title, "Title")
        self.assertEqual(item.content, "Content")
        self.assertEqual(item.source_url, "https://example.com")


class TestDatabase(unittest.TestCase):
    """Test database creation and operations"""

    def setUp(self):
        """Set up in-memory database for testing"""
        self.db = DatabaseManager(SQLite3Backend(":memory:"))
        self.db.connect()

    def tearDown(self):
        """Clean up database"""
        try:
            self.db.disconnect()
        except Exception:
            pass

    def test_database_connection(self):
        """Test database connection"""
        self.assertIsNotNone(self.db)

    def test_query_save_and_load(self):
        """Test saving and loading a query"""
        request = QueryRequest(
            query_fields=["test"],
            query_topics=["example"],
            source_agents=["TestAgent"]
        )
        saved_id = self.db.save_query(request)
        self.assertIsNotNone(saved_id)

        loaded_query = self.db.load_query(saved_id)
        self.assertIsNotNone(loaded_query)

    def test_item_save_and_load(self):
        """Test saving and loading an item"""
        item = SearchItem(
            title="Test Item",
            content="Test content",
            source_url="https://example.com",
            source_name="Example",
            source_type="TestAgent",
            timestamp=datetime.now()
        )
        saved_item_id = self.db.save_item(item)
        self.assertIsNotNone(saved_item_id)

    def test_database_backend_type(self):
        """Test that database backend is correct type"""
        self.assertIsInstance(self.db.backend, SQLite3Backend)

    def test_save_query_returns_id(self):
        """Test that save_query returns an ID"""
        request = QueryRequest(
            query_fields=["test"],
            query_topics=["example"],
            source_agents=["TestAgent"]
        )
        saved_id = self.db.save_query(request)
        self.assertIsNotNone(saved_id)
        self.assertTrue(isinstance(saved_id, (int, str)))

    def test_save_item_returns_id(self):
        """Test that save_item returns an ID"""
        item = SearchItem(
            title="Test",
            content="Test",
            source_url="https://example.com",
            source_name="Source",
            source_type="TestAgent",
            timestamp=datetime.now()
        )
        saved_id = self.db.save_item(item)
        self.assertIsNotNone(saved_id)


class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple components"""

    def test_all_components_available(self):
        """Test that all components are available"""
        # Test database
        db = DatabaseManager(SQLite3Backend(":memory:"))
        db.connect()
        self.assertIsNotNone(db)
        db.disconnect()

        # Test pipeline (requires agents dict and db_manager)
        # Use a simple agents dict - SearchPipeline expects Dict[str, SearchAgent]
        agents = {}  # Empty dict is fine for testing initialization
        db = DatabaseManager(SQLite3Backend(":memory:"))
        pipeline = SearchPipeline(agents, db)
        self.assertIsNotNone(pipeline)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
