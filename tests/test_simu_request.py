"""
Unit tests for simu_request decorator

Tests caching behavior with different flag configurations.
"""

import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from src.utils.simu_request import (
    SimuRequest,
    simu_request,
    SimuCallConfig,
)


class TestMD5Generation(unittest.TestCase):
    """Test MD5 hash generation"""

    def test_consistent_hash(self):
        """Hash should be consistent for same input"""
        hash1 = SimuRequest._generate_md5_hash("TestClass", "test_method")
        hash2 = SimuRequest._generate_md5_hash("TestClass", "test_method")
        self.assertEqual(hash1, hash2)

    def test_different_class_different_hash(self):
        """Different classes should produce different hashes"""
        hash1 = SimuRequest._generate_md5_hash("Class1", "method")
        hash2 = SimuRequest._generate_md5_hash("Class2", "method")
        self.assertNotEqual(hash1, hash2)

    def test_different_method_different_hash(self):
        """Different methods should produce different hashes"""
        hash1 = SimuRequest._generate_md5_hash("Class", "method1")
        hash2 = SimuRequest._generate_md5_hash("Class", "method2")
        self.assertNotEqual(hash1, hash2)


class TestCachePath(unittest.TestCase):
    """Test cache path generation"""

    def test_cache_path_format(self):
        """Cache path should follow correct format"""
        path = SimuRequest._get_cache_path("MyClass", "my_method", "cache_dir")
        self.assertIn("MyClass", str(path))
        self.assertIn("my_method", str(path))
        self.assertIn("cache_dir", str(path))
        self.assertTrue(str(path).endswith(".json"))

    def test_cache_path_consistency(self):
        """Cache path should be consistent for same inputs"""
        path1 = SimuRequest._get_cache_path("Class", "method", "dir")
        path2 = SimuRequest._get_cache_path("Class", "method", "dir")
        self.assertEqual(path1, path2)


class TestCacheIO(unittest.TestCase):
    """Test cache file I/O operations"""

    def setUp(self):
        """Create temporary directory for test cache"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory"""
        self.temp_dir.cleanup()

    def test_save_and_load_cache(self):
        """Save and load cache should work correctly"""
        cache_file = self.temp_path / "test_cache.json"
        test_response = {"status": "success", "data": "test"}

        # Save
        success = SimuRequest._save_cached_response(cache_file, test_response)
        self.assertTrue(success)
        self.assertTrue(cache_file.exists())

        # Load
        loaded = SimuRequest._load_cached_response(cache_file)
        self.assertEqual(loaded, test_response)

    def test_load_nonexistent_cache(self):
        """Loading nonexistent cache should return None"""
        cache_file = self.temp_path / "nonexistent.json"
        loaded = SimuRequest._load_cached_response(cache_file)
        self.assertIsNone(loaded)

    def test_save_creates_directory(self):
        """Saving should create directory if it doesn't exist"""
        cache_file = self.temp_path / "subdir" / "test.json"
        test_response = {"test": "data"}

        success = SimuRequest._save_cached_response(cache_file, test_response)
        self.assertTrue(success)
        self.assertTrue(cache_file.exists())

    def test_cache_preserves_data(self):
        """Cache should preserve complex data structures"""
        cache_file = self.temp_path / "complex.json"
        complex_response = {
            "results": [
                {"id": 1, "title": "Test 1", "nested": {"value": 100}},
                {"id": 2, "title": "Test 2", "nested": {"value": 200}},
            ],
            "metadata": {"count": 2, "timestamp": "2025-11-20T00:00:00Z"}
        }

        SimuRequest._save_cached_response(cache_file, complex_response)
        loaded = SimuRequest._load_cached_response(cache_file)
        self.assertEqual(loaded, complex_response)


class TestCacheFileContent(unittest.TestCase):
    """Test cache file content structure with request metadata and timestamp"""

    def setUp(self):
        """Create temporary directory for test cache"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory"""
        self.temp_dir.cleanup()

    def test_cache_file_has_all_required_fields(self):
        """Cache file should contain response, request, and timestamp fields"""
        cache_file = self.temp_path / "metadata_test.json"
        test_response = {"code": 200, "data": "test"}
        test_metadata = {
            "url": "https://api.example.com/search",
            "method": "POST",
            "json": {"query": "test"},
            "headers": {"Authorization": "Bearer token"},
            "timeout": 30
        }

        SimuRequest._save_cached_response(cache_file, test_response, test_metadata)

        # Load raw JSON to check structure
        with open(cache_file, 'r') as f:
            cached_data = json.load(f)

        # Verify top-level fields
        self.assertIn("response", cached_data)
        self.assertIn("request", cached_data)
        self.assertIn("timestamp", cached_data)

    def test_response_field_preserves_data(self):
        """Response field should preserve original response data"""
        cache_file = self.temp_path / "response_test.json"
        test_response = {
            "code": 200,
            "message": "success",
            "results": [{"id": 1, "name": "Item 1"}]
        }

        SimuRequest._save_cached_response(cache_file, test_response)

        with open(cache_file, 'r') as f:
            cached_data = json.load(f)

        self.assertEqual(cached_data["response"], test_response)

    def test_request_field_contains_url(self):
        """Request field should contain url"""
        cache_file = self.temp_path / "request_url_test.json"
        test_response = {"status": "ok"}
        test_metadata = {
            "url": "https://api.example.com/v1/search",
            "method": "POST"
        }

        SimuRequest._save_cached_response(cache_file, test_response, test_metadata)

        with open(cache_file, 'r') as f:
            cached_data = json.load(f)

        self.assertEqual(cached_data["request"]["url"], "https://api.example.com/v1/search")

    def test_request_field_contains_method(self):
        """Request field should contain HTTP method"""
        cache_file = self.temp_path / "request_method_test.json"
        test_response = {"status": "ok"}
        test_metadata = {
            "url": "https://api.example.com/search",
            "method": "POST"
        }

        SimuRequest._save_cached_response(cache_file, test_response, test_metadata)

        with open(cache_file, 'r') as f:
            cached_data = json.load(f)

        self.assertEqual(cached_data["request"]["method"], "POST")

    def test_request_field_contains_json_body(self):
        """Request field should contain JSON request body"""
        cache_file = self.temp_path / "request_json_test.json"
        test_response = {"status": "ok"}
        request_body = {"query": "artificial intelligence", "limit": 10}
        test_metadata = {
            "url": "https://api.example.com/search",
            "method": "POST",
            "json": request_body
        }

        SimuRequest._save_cached_response(cache_file, test_response, test_metadata)

        with open(cache_file, 'r') as f:
            cached_data = json.load(f)

        self.assertEqual(cached_data["request"]["json"], request_body)

    def test_request_field_contains_headers(self):
        """Request field should contain request headers"""
        cache_file = self.temp_path / "request_headers_test.json"
        test_response = {"status": "ok"}
        headers = {
            "Authorization": "Bearer token123",
            "Content-Type": "application/json"
        }
        test_metadata = {
            "url": "https://api.example.com/search",
            "method": "POST",
            "headers": headers
        }

        SimuRequest._save_cached_response(cache_file, test_response, test_metadata)

        with open(cache_file, 'r') as f:
            cached_data = json.load(f)

        self.assertEqual(cached_data["request"]["headers"], headers)

    def test_request_field_contains_timeout(self):
        """Request field should contain timeout value"""
        cache_file = self.temp_path / "request_timeout_test.json"
        test_response = {"status": "ok"}
        test_metadata = {
            "url": "https://api.example.com/search",
            "method": "POST",
            "timeout": 30
        }

        SimuRequest._save_cached_response(cache_file, test_response, test_metadata)

        with open(cache_file, 'r') as f:
            cached_data = json.load(f)

        self.assertEqual(cached_data["request"]["timeout"], 30)

    def test_timestamp_has_correct_format(self):
        """Timestamp should be ISO 8601 format ending with Z"""
        cache_file = self.temp_path / "timestamp_format_test.json"
        test_response = {"status": "ok"}

        SimuRequest._save_cached_response(cache_file, test_response)

        with open(cache_file, 'r') as f:
            cached_data = json.load(f)

        timestamp = cached_data["timestamp"]

        # Check format: YYYY-MM-DDTHH:MM:SS.ffffffZ
        self.assertRegex(timestamp, r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z$')
        self.assertTrue(timestamp.endswith("Z"))

    def test_timestamp_is_recent(self):
        """Timestamp should be recent (within last minute)"""
        from datetime import datetime, timezone, timedelta

        cache_file = self.temp_path / "timestamp_recent_test.json"
        test_response = {"status": "ok"}

        before_save = datetime.now(timezone.utc)
        SimuRequest._save_cached_response(cache_file, test_response)
        after_save = datetime.now(timezone.utc)

        with open(cache_file, 'r') as f:
            cached_data = json.load(f)

        timestamp_str = cached_data["timestamp"]
        # Parse timestamp (remove Z and parse)
        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

        # Timestamp should be between before_save and after_save
        self.assertGreaterEqual(timestamp, before_save - timedelta(seconds=1))
        self.assertLessEqual(timestamp, after_save + timedelta(seconds=1))

    def test_complete_request_args_preserved(self):
        """Complete request arguments should be preserved in cache"""
        cache_file = self.temp_path / "complete_request_test.json"
        test_response = {
            "status": "success",
            "articles": [
                {"id": 1, "title": "Article 1"}
            ]
        }
        complete_metadata = {
            "url": "https://api.bochaai.com/v1/web-search",
            "method": "POST",
            "json": {
                "query": "machine learning",
                "freshness": "oneWeek",
                "count": 20
            },
            "headers": {
                "Authorization": "Bearer sk-xxx",
                "User-Agent": "NewsAgent/1.0"
            },
            "timeout": 30
        }

        SimuRequest._save_cached_response(cache_file, test_response, complete_metadata)

        with open(cache_file, 'r') as f:
            cached_data = json.load(f)

        # Verify all request fields
        request = cached_data["request"]
        self.assertEqual(request["url"], "https://api.bochaai.com/v1/web-search")
        self.assertEqual(request["method"], "POST")
        self.assertEqual(request["json"]["query"], "machine learning")
        self.assertEqual(request["json"]["count"], 20)
        self.assertEqual(request["headers"]["Authorization"], "Bearer sk-xxx")
        self.assertEqual(request["timeout"], 30)

    def test_empty_metadata_handled_gracefully(self):
        """Empty metadata should be saved as empty dict"""
        cache_file = self.temp_path / "empty_metadata_test.json"
        test_response = {"status": "ok"}

        # Save with no metadata
        SimuRequest._save_cached_response(cache_file, test_response, None)

        with open(cache_file, 'r') as f:
            cached_data = json.load(f)

        self.assertEqual(cached_data["request"], {})
        self.assertEqual(cached_data["response"], test_response)
        self.assertIn("timestamp", cached_data)

    def test_json_serialization_with_unicode(self):
        """Cache should handle Unicode in request and response"""
        cache_file = self.temp_path / "unicode_test.json"
        test_response = {
            "status": "成功",
            "results": ["人工智能", "机器学习"]
        }
        test_metadata = {
            "url": "https://api.example.com/search",
            "method": "POST",
            "json": {"query": "人工智能"}
        }

        SimuRequest._save_cached_response(cache_file, test_response, test_metadata)

        with open(cache_file, 'r', encoding='utf-8') as f:
            cached_data = json.load(f)

        self.assertEqual(cached_data["response"]["status"], "成功")
        self.assertEqual(cached_data["request"]["json"]["query"], "人工智能")


class TestSimuRequestConfig(unittest.TestCase):
    """Test SimuRequest configuration loading and behavior"""

    def setUp(self):
        """Reset configuration before each test"""
        SimuRequest.reload()

    def tearDown(self):
        """Reset configuration after each test"""
        SimuRequest.reload()

    def test_config_defaults(self):
        """Config should have sensible defaults"""
        config = SimuRequest.status()
        # persist_dir should be an absolute path containing 'data/simu_responses'
        persist_dir = config.get("persist_dir")
        self.assertIsNotNone(persist_dir)
        self.assertTrue(persist_dir.endswith("data/simu_responses"))
        self.assertIsNotNone(config.get("simu_call"))
        self.assertIsNotNone(config.get("update_response"))

    def test_update_behaviors_method(self):
        """update_behaviors() should modify flags"""
        original = SimuRequest.status()

        # Disable logging to avoid output during test
        SimuRequest.update_behaviors(log_calls=0, verbose=False)

        # Update simu_call
        SimuRequest.update_behaviors(simu_call=1, verbose=False)
        config = SimuRequest.status()
        self.assertEqual(config.get("simu_call"), 1)

        # Reset
        SimuRequest.update_behaviors(simu_call=original["simu_call"], verbose=False)

    def test_status_returns_config_dict(self):
        """status() should return all config values"""
        config_dict = SimuRequest.status()
        self.assertIn("simu_call", config_dict)
        self.assertIn("update_response", config_dict)
        self.assertIn("persist_dir", config_dict)
        self.assertIn("log_calls", config_dict)


class TestSimuCallConfig(unittest.TestCase):
    """Test backward compatibility with SimuCallConfig (DEPRECATED)"""

    def test_backward_compat_get(self):
        """SimuCallConfig.get() should work (deprecated)"""
        config = SimuCallConfig()
        result = config.get("simu_call")
        self.assertIsNotNone(result)

    def test_backward_compat_set(self):
        """SimuCallConfig.set() should work (deprecated)"""
        config = SimuCallConfig()
        original = config.get("simu_call")

        # Disable logging to avoid output during test
        SimuRequest.update_behaviors(log_calls=0, verbose=False)

        config.set("simu_call", 1)
        self.assertEqual(config.get("simu_call"), 1)

        config.set("simu_call", original)
        self.assertEqual(config.get("simu_call"), original)


class TestSimuRequestDecorator(unittest.TestCase):
    """Test SimuRequest.simu_request decorator functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        # Reset config
        SimuRequest.reload()

    def tearDown(self):
        """Clean up"""
        self.temp_dir.cleanup()
        SimuRequest.reload()

    def test_decorator_calls_function(self):
        """Decorator should call the decorated function"""
        call_count = [0]

        class TestClass:
            @SimuRequest.simu_request
            def test_method(self, param):
                call_count[0] += 1
                return {"result": param}

        obj = TestClass()
        # Disable caching for this test
        SimuRequest.update_behaviors(simu_call=0, update_response=0, log_calls=0, verbose=False)

        result = obj.test_method("test_value")
        self.assertEqual(call_count[0], 1)
        self.assertEqual(result["result"], "test_value")

    def test_caching_behavior(self):
        """Test caching on/off behavior"""
        call_count = [0]

        class TestClass:
            @SimuRequest.simu_request
            def method(self, x):
                call_count[0] += 1
                return {"value": x, "call": call_count[0]}

        # Patch cache path to use temp directory
        with patch('src.utils.simu_request.SimuRequest._get_cache_path') as mock_path:
            cache_file = self.temp_path / "cache.json"
            mock_path.return_value = cache_file

            # First, capture mode (call and save)
            SimuRequest.update_behaviors(simu_call=0, update_response=1, log_calls=0, verbose=False)

            obj = TestClass()

            # First call - should cache
            result1 = obj.method(42)
            self.assertEqual(result1["call"], 1)

            # Enable caching mode
            SimuRequest.update_behaviors(simu_call=1, update_response=0, verbose=False)

            # Second call - should use cache
            result2 = obj.method(42)
            self.assertEqual(result2["call"], 1)  # Same as first (from cache)
            self.assertEqual(call_count[0], 1)  # Still only called once

    def test_exception_handling(self):
        """Decorator should propagate exceptions"""
        class TestClass:
            @SimuRequest.simu_request
            def method(self):
                raise ValueError("Test error")

        SimuRequest.update_behaviors(simu_call=0, update_response=0, log_calls=0, verbose=False)

        obj = TestClass()
        with self.assertRaises(ValueError):
            obj.method()


if __name__ == '__main__':
    unittest.main()
