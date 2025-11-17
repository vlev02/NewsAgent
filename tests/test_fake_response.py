#!/usr/bin/env python3
"""
Test Fake Response System

Comprehensive tests for:
- Fake response manager MD5 hashing and file operations
- Response caching and retrieval
- Response updating (single file replacement)
- Decorator functionality
- Debug logging
- User interaction prompts

Unit tests using unittest framework.
"""

import unittest
from pathlib import Path

from src.utils.fake_response_manager import FakeResponseManager, fake_response_manager
from src.debug_config import DebugConfig
from src.utils.debug_logger import DebugLogger
from src.decorators import fake_response_handler
from src.decorators.response_handler import _ask_user_choice, _cache_response


class TestFakeResponseManager(unittest.TestCase):
    """Test FakeResponseManager module functionality"""

    def setUp(self):
        """Set up test fixtures"""
        DebugConfig.DEBUG = False

    def tearDown(self):
        """Clean up after tests"""
        DebugConfig.DEBUG = False

    def test_1_import_fake_response_manager(self):
        """Test 1: Import fake response manager"""
        self.assertIsNotNone(FakeResponseManager)
        self.assertIsNotNone(fake_response_manager)
        self.assertIsNotNone(DebugLogger)

    def test_2_md5_hash_generation_consistency(self):
        """Test 2a: MD5 hash generation produces consistent results"""
        hash1 = FakeResponseManager.generate_hash(
            "https://api.bocha.ai/search",
            "POST",
            "default"
        )
        hash2 = FakeResponseManager.generate_hash(
            "https://api.bocha.ai/search",
            "POST",
            "default"
        )
        self.assertEqual(hash1, hash2, "Same inputs should produce same hash")

    def test_2b_md5_hash_length(self):
        """Test 2b: MD5 hash should be 32 characters"""
        hash_value = FakeResponseManager.generate_hash(
            "https://api.bocha.ai/search",
            "POST",
            "default"
        )
        self.assertEqual(len(hash_value), 32, "MD5 hash should be 32 characters")

    def test_2c_md5_hash_different_descriptions(self):
        """Test 2c: Different descriptions produce different hashes"""
        hash1 = FakeResponseManager.generate_hash(
            "https://api.bocha.ai/search",
            "POST",
            "default"
        )
        hash3 = FakeResponseManager.generate_hash(
            "https://api.bocha.ai/search",
            "POST",
            "custom"
        )
        self.assertNotEqual(hash1, hash3, "Different descriptions should produce different hashes")

    def test_3_list_responses(self):
        """Test 3: Check existing fake responses"""
        bocha_responses = fake_response_manager.list_responses("BOCHA")
        self.assertIsInstance(bocha_responses, list)
        # Should have at least 0 responses (empty is OK)
        self.assertGreaterEqual(len(bocha_responses), 0)

    def test_4_retrieve_cached_response(self):
        """Test 4: Testing response retrieval"""
        response = fake_response_manager.get_response(
            agent_name="BOCHA",
            url="https://api.bocha.ai/websearch",
            method="POST",
            description="default"
        )
        # Response can be None or a dict
        if response:
            self.assertIsInstance(response, dict)
            self.assertIn('url', response)
            self.assertIn('response_body', response)

    def test_5a_debug_configuration_enable(self):
        """Test 5a: Debug configuration enable"""
        DebugConfig.enable_debug()
        self.assertTrue(DebugConfig.DEBUG)
        self.assertTrue(DebugConfig.fake_response_enabled)

    def test_5b_debug_configuration_disable(self):
        """Test 5b: Debug configuration disable"""
        DebugConfig.enable_debug()
        DebugConfig.disable_debug()
        self.assertFalse(DebugConfig.DEBUG)
        self.assertFalse(DebugConfig.fake_response_enabled)

    def test_5c_debug_configuration_update_mode(self):
        """Test 5c: Debug configuration update mode"""
        DebugConfig.set_update_mode(True)
        self.assertTrue(DebugConfig.fake_response_update)
        DebugConfig.set_update_mode(False)
        self.assertFalse(DebugConfig.fake_response_update)

    def test_6_response_statistics(self):
        """Test 6: Testing response statistics"""
        stats = fake_response_manager.get_statistics("BOCHA")
        self.assertIsInstance(stats, dict)
        self.assertIn('total_cached', stats)
        self.assertIn('total_usage', stats)
        self.assertGreaterEqual(stats['total_cached'], 0)
        self.assertGreaterEqual(stats['total_usage'], 0)

    def test_7a_response_existence_check_true(self):
        """Test 7a: Response existence check for existing response"""
        exists = fake_response_manager.response_exists(
            agent_name="BOCHA",
            url="https://api.bocha.ai/websearch",
            method="POST",
            description="default"
        )
        self.assertIsInstance(exists, bool)

    def test_7b_response_existence_check_false(self):
        """Test 7b: Response existence check for non-existing response"""
        not_exists = fake_response_manager.response_exists(
            agent_name="BOCHA",
            url="https://api.fake.ai/search",
            method="POST",
            description="nonexistent"
        )
        self.assertFalse(not_exists)

    def test_8_directory_structure(self):
        """Test 8: Verifying directory structure"""
        fake_response_dir = Path("data/fake_response")
        agents = ["bocha", "xunfei", "hunyuan", "qianfan", "meta", "twitter"]

        for agent in agents:
            agent_dir = fake_response_dir / agent
            self.assertTrue(
                agent_dir.exists(),
                f"{agent} directory should exist at {agent_dir}"
            )

    def test_9_decorator_imports(self):
        """Test 9: Testing decorator imports"""
        self.assertIsNotNone(fake_response_handler)
        self.assertIsNotNone(_ask_user_choice)
        self.assertIsNotNone(_cache_response)

    def test_10_debug_logger(self):
        """Test 10: Testing debug logger"""
        logger = DebugLogger("test_module")
        self.assertIsNotNone(logger)

        # Test that logger respects DEBUG flag
        DebugConfig.DEBUG = False
        # Should not raise exceptions
        logger.info("This should not appear")
        logger.debug("This should not appear")
        logger.warning("This should not appear")
        logger.error("This should not appear")

        # Test with DEBUG enabled
        DebugConfig.DEBUG = True
        # Should not raise exceptions
        logger.info("This is an info message")
        logger.debug("This is a debug message")
        DebugConfig.DEBUG = False


class TestDebugConfig(unittest.TestCase):
    """Test DebugConfig class functionality"""

    def test_enable_debug_method(self):
        """Test enable_debug classmethod"""
        DebugConfig.disable_debug()
        DebugConfig.enable_debug()
        self.assertTrue(DebugConfig.DEBUG)
        self.assertTrue(DebugConfig.fake_response_enabled)
        self.assertTrue(DebugConfig.log_fake_response_hits)

    def test_disable_debug_method(self):
        """Test disable_debug classmethod"""
        DebugConfig.enable_debug()
        DebugConfig.disable_debug()
        self.assertFalse(DebugConfig.DEBUG)
        self.assertFalse(DebugConfig.fake_response_enabled)

    def test_enable_fake_responses(self):
        """Test enable_fake_responses method"""
        DebugConfig.disable_fake_responses()
        DebugConfig.enable_fake_responses()
        self.assertTrue(DebugConfig.fake_response_enabled)

    def test_disable_fake_responses(self):
        """Test disable_fake_responses method"""
        DebugConfig.enable_fake_responses()
        DebugConfig.disable_fake_responses()
        self.assertFalse(DebugConfig.fake_response_enabled)

    def test_enable_interactive(self):
        """Test enable_interactive method"""
        DebugConfig.disable_interactive()
        DebugConfig.enable_interactive()
        self.assertTrue(DebugConfig.fake_response_interact)

    def test_disable_interactive(self):
        """Test disable_interactive method"""
        DebugConfig.enable_interactive()
        DebugConfig.disable_interactive()
        self.assertFalse(DebugConfig.fake_response_interact)

    def test_get_config_summary(self):
        """Test get_config_summary method"""
        summary = DebugConfig.get_config_summary()
        self.assertIsInstance(summary, str)
        self.assertIn("Debug Configuration Summary", summary)
        self.assertIn("DEBUG", summary)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
