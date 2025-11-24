"""Test suite for independent DataManager module

Tests:
- DataManager singleton
- Data model persistence (Request, ResponseItem)
- Cascade deletion
- Agent wrapper integration
- CASE parsers for different agent types

Uses temporary databases to isolate tests.
"""

import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data_manager import (
    get_data_manager, DataManager, DataModelType,
    RequestModel, ResponseItem, AgentDataWrapper
)
from src.data_manager.config import create_test_config
import src.data_manager.manager as dm_module


class DataManagerTestBase(unittest.TestCase):
    """Base class for DataManager tests"""

    def setUp(self):
        """Reset singleton and use temporary database for each test"""
        # Reset singleton and initialized flag
        if DataManager._instance:
            DataManager._instance._initialized = False
        DataManager._instance = None
        DataManager._test_config = None

        # Create temporary database for this test
        self.temp_dir = tempfile.TemporaryDirectory()
        temp_path = Path(self.temp_dir.name)
        temp_path.mkdir(parents=True, exist_ok=True)
        self.temp_db_path = str(temp_path / "test_datamanager.db")

        # Set test config BEFORE creating DataManager instance
        test_config = create_test_config(self.temp_db_path)
        DataManager._test_config = test_config

        # Initialize DataManager with test config
        self.dm = get_data_manager()

    def tearDown(self):
        """Clean up temporary database after each test"""
        # Close storage connections first before cleanup
        if DataManager._instance and hasattr(DataManager._instance, 'storage'):
            try:
                # SQLiteBackend may have open connections
                # This is optional - SQLiteBackend doesn't have explicit close yet
                pass
            except Exception:
                pass

        # Reset singleton configuration and state
        DataManager._test_config = None
        if DataManager._instance:
            DataManager._instance._initialized = False
        DataManager._instance = None

        # Reset module-level singleton in manager.py
        dm_module._data_manager = None

        # Clean up temp directory (context manager handles cleanup)
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass  # Ignore cleanup errors


class TestDataManagerSingleton(DataManagerTestBase):
    """Test DataManager singleton pattern"""

    def test_singleton_instance(self):
        """Test that get_data_manager returns same instance"""
        dm1 = self.dm
        dm2 = get_data_manager()
        self.assertIs(dm1, dm2)

    def test_models_list(self):
        """Test models() returns all available models"""
        models = self.dm.models()
        self.assertEqual(set(models), {
            'request_model',
            'response_item'
        })


class TestRequestModelPersistence(DataManagerTestBase):
    """Test RequestModel recording and retrieval"""

    def test_record_request(self):
        """Test recording a RequestModel"""
        request_data = {
            'agent_name': 'BOCHA',
            'url': 'https://api.bochaai.com/v1/web-search',
            'method': 'POST',
            'headers': {'Authorization': 'Bearer test-key'},
            'body': {'query': 'AI news'},
            'raw_response': {'items': [{'title': 'AI News'}]},
            'http_status': 200,
            'execution_time_ms': 1234,
            'success': True
        }

        request_id = self.dm.record(DataModelType.REQUEST, request_data)
        self.assertIsNotNone(request_id)
        self.assertTrue(len(request_id) > 0)

    def test_retrieve_request(self):
        """Test retrieving a recorded RequestModel"""
        request_data = {
            'agent_name': 'BOCHA',
            'url': 'https://api.bochaai.com/v1/web-search',
            'method': 'POST',
            'headers': {'Authorization': 'Bearer key'},
            'body': {'query': 'test'},
            'http_status': 200,
            'success': True
        }

        request_id = self.dm.record(DataModelType.REQUEST, request_data)
        retrieved = self.dm.retrieve(DataModelType.REQUEST, request_id)

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['agent_name'], 'BOCHA')
        self.assertEqual(retrieved['http_status'], 200)

    def test_explore_requests(self):
        """Test exploring request statistics"""
        # Get initial count
        initial_report = self.dm.explore(DataModelType.REQUEST)
        initial_total = initial_report['total']

        # Record multiple requests
        for agent in ['BOCHA', 'XUNFEI', 'BOCHA']:
            self.dm.record(DataModelType.REQUEST, {
                'agent_name': agent,
                'url': f'https://api.{agent.lower()}.com',
                'method': 'POST',
                'headers': {},
                'body': {},
                'success': True
            })

        report = self.dm.explore(DataModelType.REQUEST)

        # Verify 3 new records were added
        self.assertEqual(report['total'], initial_total + 3)
        # Verify BOCHA and XUNFEI are in the stats
        self.assertIn('BOCHA', report['by_agent'])
        self.assertIn('XUNFEI', report['by_agent'])
        self.assertTrue(len(report['sample_keys']) > 0)


class TestResponseItemWithCascade(DataManagerTestBase):
    """Test ResponseItem recording with cascade to RequestModel"""

    def test_record_response_items(self):
        """Test recording multiple ResponseItems linked to RequestModel"""
        # Setup cascade
        request_id = self.dm.record(DataModelType.REQUEST, {
            'agent_name': 'BOCHA',
            'url': 'https://api.bochaai.com',
            'method': 'POST',
            'headers': {},
            'body': {'query': 'AI'},
            'success': True
        })

        request_model = RequestModel(request_id=request_id, agent_name='BOCHA')

        # Record response items
        item_ids = []

        for i in range(3):
            item_id = self.dm.record(DataModelType.RESPONSE_ITEM, {
                'agent_name': 'BOCHA',
                'title': f'AI News {i}',
                'content': f'Content about AI {i}',
                'source_url': f'https://example.com/{i}',
                'source_name': 'Example',
                'significance': 'high'
            }, associated_case=request_model)
            item_ids.append(item_id)

        self.assertEqual(len(item_ids), 3)

    def test_retrieve_response_item(self):
        """Test retrieving a recorded ResponseItem"""
        # Setup cascade
        request_id = self.dm.record(DataModelType.REQUEST, {
            'agent_name': 'META',
            'url': 'https://metaso.cn/api/v1/search',
            'method': 'POST',
            'headers': {},
            'body': {},
            'success': True
        })

        request_model = RequestModel(request_id=request_id, agent_name='META')
        item_id = self.dm.record(DataModelType.RESPONSE_ITEM, {
            'agent_name': 'META',
            'title': 'Breaking News',
            'content': 'Important announcement',
            'source_url': 'https://news.com/123',
            'source_name': 'News Site',
            'key_entities': ['Company A', 'CEO'],
            'relevance_score': 0.95
        }, associated_case=request_model)

        # Retrieve
        retrieved = self.dm.retrieve(DataModelType.RESPONSE_ITEM, item_id)

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['title'], 'Breaking News')
        self.assertEqual(retrieved['request_id'], request_id)
        self.assertEqual(retrieved['relevance_score'], 0.95)


class TestAgentDataWrapper(DataManagerTestBase):
    """Test AgentDataWrapper mixin for agents"""

    def test_wrapper_parse_request(self):
        """Test parse_request method"""
        # Mock agent class
        class MockAgent(AgentDataWrapper):
            NAME = "BOCHA"
            api_endpoint = "https://api.bochaai.com/v1/web-search"
            request_body = {"query": "AI news"}

            def get_header_dict(self):
                return {"Authorization": "Bearer key"}

        agent = MockAgent()

        # Parse request
        request_data = agent.parse_request(
            method="POST",
            http_status=200,
            execution_time_ms=1500,
            success=True
        )

        self.assertEqual(request_data['agent_name'], 'BOCHA')
        self.assertEqual(request_data['url'], 'https://api.bochaai.com/v1/web-search')
        self.assertEqual(request_data['method'], 'POST')
        self.assertEqual(request_data['http_status'], 200)
        self.assertEqual(request_data['execution_time_ms'], 1500)

    def test_wrapper_parse_response_items(self):
        """Test parse_response_items with custom parser"""
        class MockAgent(AgentDataWrapper):
            NAME = "BOCHA"
            api_endpoint = "https://api.bochaai.com"
            request_body = {}

            def get_header_dict(self):
                return {}

            def _extract_response_items(self, raw_response):
                """Extract items from BOCHA response"""
                return raw_response.get('webPages', [])

            def _parse_response_item(self, item_data):
                """Parse BOCHA item"""
                return {
                    'title': item_data.get('name'),
                    'content': item_data.get('snippet'),
                    'source_url': item_data.get('url'),
                    'source_name': 'BOCHA',
                    'agent_metadata': item_data
                }

        agent = MockAgent()

        # Parse response
        raw_response = {
            'webPages': [
                {'name': 'AI News 1', 'snippet': 'Content 1', 'url': 'https://ex1.com'},
                {'name': 'AI News 2', 'snippet': 'Content 2', 'url': 'https://ex2.com'}
            ]
        }

        items = agent.parse_response_items(raw_response)

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['title'], 'AI News 1')
        self.assertEqual(items[1]['source_url'], 'https://ex2.com')

    def test_wrapper_parse_response_items_bocha_dispatch(self):
        """Ensure BOCHA responses are parsed via agent-specific dispatcher."""

        class MockBochaAgent(AgentDataWrapper):
            NAME = "BOCHA"
            api_endpoint = "https://api.bochaai.com"
            request_body = {}

            def get_header_dict(self):
                return {}

        agent = MockBochaAgent()
        raw_response = {
            "code": 200,
            "data": {
                "webPages": {
                    "value": [
                        {
                            "name": "Example Title",
                            "snippet": "Example summary",
                            "url": "https://example.com",
                            "siteName": "ExampleSite",
                            "datePublished": "2025-11-18T12:03:08+08:00",
                            "contractedEntities": [{"name": "EntityA"}],
                        },
                        {
                            "name": "Another Result",
                            "summary": "Another summary",
                            "url": "https://example.org",
                            "siteName": "ExampleOrg",
                        },
                    ]
                }
            },
        }

        items = agent.parse_response_items(raw_response)

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['source_name'], 'ExampleSite')
        self.assertIn('EntityA', items[0]['key_entities'])

    def test_wrapper_parse_response_items_xunfei_structured_json(self):
        """Ensure XUNFEI structured JSON is parsed correctly."""

        class MockXunfeiAgent(AgentDataWrapper):
            NAME = "XUNFEI"
            api_endpoint = "https://api.example.com"
            request_body = {}

            def get_header_dict(self):
                return {}

        agent = MockXunfeiAgent()
        structured = {
            "search_date": "2025-11-21",
            "summary": "test",
            "news_items": [
                {
                    "title": "Test Title",
                    "content": "Detailed content",
                    "source_link": "https://example.com",
                    "category": "AI",
                    "key_entities": ["Entity1"],
                    "significance": "高",
                    "timestamp": "2025-11-21 12:00",
                }
            ],
        }
        raw_response = {
            "response": {
                "choices": [
                    {
                        "message": {
                            "content": "```json\n" + json.dumps(structured) + "\n```"
                        }
                    }
                ]
            }
        }

        items = agent.parse_response_items(raw_response)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['title'], "Test Title")
        self.assertEqual(items[0]['source_url'], "https://example.com")


class TestDataManagerWithWrapper(DataManagerTestBase):
    """Test integration of AgentDataWrapper with DataManager"""

    def test_full_workflow_with_agent(self):
        """Test complete workflow: agent -> wrapper -> data_manager"""
        # Mock agent with wrapper
        class BochaAgent(AgentDataWrapper):
            NAME = "BOCHA"
            api_endpoint = "https://api.bochaai.com/v1/web-search"
            request_body = {"query": "artificial intelligence"}

            def get_header_dict(self):
                return {"Authorization": "Bearer bocha-key"}

            def _extract_response_items(self, raw_response):
                return raw_response.get('webPages', [])

            def _parse_response_item(self, item_data):
                return {
                    'title': item_data.get('name'),
                    'content': item_data.get('snippet'),
                    'source_url': item_data.get('url'),
                    'source_name': 'BOCHA',
                    'key_entities': [],
                    'agent_metadata': item_data
                }

        agent = BochaAgent()

        # Step 1: Record request
        request_data = agent.parse_request(
            http_status=200,
            execution_time_ms=2000,
            success=True
        )
        request_id = self.dm.record(DataModelType.REQUEST, request_data)

        request_model = RequestModel(request_id=request_id, agent_name='BOCHA')

        # Step 2: Record response items
        raw_response = {
            'webPages': [
                {'name': 'AI Break', 'snippet': 'Breaking AI news', 'url': 'https://ex.com/1'},
                {'name': 'AI Trends', 'snippet': 'Latest AI trends', 'url': 'https://ex.com/2'}
            ]
        }

        items = agent.parse_response_items(raw_response)
        item_ids = []

        for item_data in items:
            item_id = self.dm.record(DataModelType.RESPONSE_ITEM, item_data, associated_case=request_model)
            item_ids.append(item_id)

        # Verify all records
        self.assertIsNotNone(self.dm.retrieve(DataModelType.REQUEST, request_id))
        for item_id in item_ids:
            self.assertIsNotNone(self.dm.retrieve(DataModelType.RESPONSE_ITEM, item_id))


class TestDataManagerAssociationValidation(DataManagerTestBase):
    """Test association validation (required associations)"""

    def test_response_item_requires_request_association(self):
        """Test that recording ResponseItem without RequestModel raises error"""
        with self.assertRaises(ValueError) as ctx:
            self.dm.record(DataModelType.RESPONSE_ITEM, {'agent_name': 'BOCHA'})

        self.assertIn('RequestModel', str(ctx.exception))


class TestSmartQuery(DataManagerTestBase):
    """Test smart_query method with multiple use cases"""

    def test_smart_query_empty_returns_statistics(self):
        """Use case 1: Empty query returns statistics dict"""
        # Get initial stats
        initial_result = self.dm.smart_query()

        # Verify result is dict with model names as keys
        self.assertIsInstance(initial_result, dict)
        self.assertIn('request_model', initial_result)
        self.assertIn('response_item', initial_result)

        # All values should be integers
        for model_name, count in initial_result.items():
            self.assertIsInstance(count, int)
            self.assertGreaterEqual(count, 0)

    def test_smart_query_empty_dict_returns_statistics(self):
        """Use case 1: Empty dict query also returns statistics"""
        result = self.dm.smart_query({})
        self.assertIsInstance(result, dict)
        self.assertIn('request_model', result)

    def test_smart_query_latest_cases(self):
        """Use case 2: Dict query with int returns latest N cases"""
        # Record test data
        request_id = self.dm.record(DataModelType.REQUEST, {
            'agent_name': 'BOCHA',
            'url': 'https://api.bochaai.com',
            'method': 'POST',
            'headers': {},
            'body': {'query': 'test'},
            'success': True
        })

        request_model = RequestModel(request_id=request_id, agent_name='BOCHA')
        item_id = self.dm.record(DataModelType.RESPONSE_ITEM, {
            'agent_name': 'BOCHA',
            'title': 'Result',
            'content': 'Body',
            'source_url': 'https://example.com',
            'source_name': 'Example'
        }, associated_case=request_model)

        # Query latest 1 request and 1 response item using int values
        result = self.dm.smart_query({
            'request_model': 1,
            'response_item': 1
        })

        self.assertIn('request_model', result)
        self.assertIn('response_item', result)
        self.assertEqual(len(result['request_model']), 1)
        self.assertEqual(len(result['response_item']), 1)
        self.assertEqual(result['request_model'][0]['request_id'], request_id)
        self.assertEqual(result['response_item'][0]['request_id'], request_id)
        self.assertEqual(result['response_item'][0]['item_id'], item_id)

    def test_smart_query_cascaded_request_to_items(self):
        """Use case 3: REQUEST ID dict returns associated RESPONSE_ITEMs"""
        # Setup: Create request with associated response items
        request_id = self.dm.record(DataModelType.REQUEST, {
            'agent_name': 'META',
            'url': 'https://metaso.cn/api',
            'method': 'POST',
            'headers': {},
            'body': {'query': 'news'},
            'success': True
        })

        request_model = RequestModel(request_id=request_id, agent_name='META')

        # Create multiple response items for this request
        item_ids = []
        for i in range(2):
            iid = self.dm.record(DataModelType.RESPONSE_ITEM, {
                'agent_name': 'META',
                'title': f'News {i}',
                'content': f'Body {i}',
                'source_url': f'https://example.com/{i}',
                'source_name': 'Example'
            }, associated_case=request_model)
            item_ids.append(iid)

        # Query with REQUEST ID dict format should return associated RESPONSE_ITEMs
        result = self.dm.smart_query({'request_model': request_id})

        self.assertIn('request_model', result)
        # The result should be a list of response items
        items = result['request_model']
        self.assertEqual(len(items), 2)
        returned_item_ids = [item['item_id'] for item in items]
        for iid in item_ids:
            self.assertIn(iid, returned_item_ids)

    def test_smart_query_cascaded_nonexistent_id(self):
        """Test cascaded query with non-existent REQUEST ID"""
        fake_id = 'nonexistent-uuid-12345'
        result = self.dm.smart_query({'request_model': fake_id})

        self.assertIn('request_model', result)
        # For non-existent IDs, result should contain error info
        error_info = result['request_model']
        self.assertIsInstance(error_info, dict)
        self.assertIn('error', error_info)
        self.assertIn(fake_id, error_info['error'])

    def test_smart_query_cascaded_response_item_leaf_node(self):
        """Test cascaded query on RESPONSE_ITEM (leaf node) returns error"""
        # RESPONSE_ITEM is a leaf node with no cascade
        fake_id = 'some-uuid-12345'
        result = self.dm.smart_query({'response_item': fake_id})

        self.assertIn('response_item', result)
        error_info = result['response_item']
        self.assertIsInstance(error_info, dict)
        self.assertIn('error', error_info)
        self.assertIn('leaf node', error_info['error'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
